"""
Search API routes
Supports multiple MCP providers (RollingGo, Tuniu)
"""
import json as _json
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import get_jwt_identity
from app.extensions import limiter
from app.services.hotel_provider import get_provider, get_available_providers, HotelProviderError
from app.utils import get_cache_service, generate_cache_key

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)


def _parse_json_body():
    """Parse JSON request body with multi-encoding fallback (UTF-8 → GBK)."""
    data = request.get_json(silent=True)
    if data is not None:
        return data
    # Fallback: try decoding raw body with GBK if UTF-8 fails
    raw = request.get_data()
    if raw:
        try:
            return _json.loads(raw.decode('utf-8'))
        except UnicodeDecodeError:
            try:
                result = _json.loads(raw.decode('gbk'))
                logger.warning(f"[Search] GBK fallback triggered from {request.remote_addr}")
                return result
            except Exception:
                pass
    return None


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates using haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _geocode(query: str):
    """
    Geocode a place name using Nominatim (OpenStreetMap).
    Returns (lat, lon) or None.
    """
    try:
        import httpx
        r = httpx.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': query, 'format': 'json', 'limit': 1, 'accept-language': 'zh'},
            headers={'User-Agent': 'HotelSearch/1.0'},
            timeout=10.0,
        )
        data = r.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        logger.warning(f'Geocoding failed for "{query}": {e}')
    return None


def _check_search_quota():
    """
    Check search quota for current user.
    Returns (user, remaining_count) or None for anonymous users.
    Raises quota exceeded error if limit reached.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
    except Exception:
        return None

    from app.models.database import db, User
    from app.routes.membership import _check_membership, _get_search_remaining

    user = _check_membership(int(user_id))
    if not user:
        return None

    remaining = _get_search_remaining(user)
    if remaining == 0:
        return None  # Will be handled after response is built
    return user


@search_bp.route('/search', methods=['POST'])
@limiter.limit("10 per minute")
def search_hotels():
    """
    Search for hotels.

    Supports multiple providers:
    - RollingGo: Global hotel search (no booking support)
    - Tuniu: Domestic hotel search with booking support

    Request body:
        - provider: Provider name ('rollinggo' or 'tuniu', default: 'tuniu')

        For RollingGo:
        - query: Search query text (required)
        - place: Destination place name (required)
        - place_type: Type of place (required)
        - check_in_date: Check-in date YYYY-MM-DD
        - stay_nights: Number of nights (default: 1)
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)
        - child_ages: List of children's ages
        - star_ratings: Star rating range e.g. "4.0,5.0"
        - max_price: Maximum price per night
        - distance: Maximum distance in meters
        - required_tags: Tags that must be present
        - preferred_tags: Tags to prefer
        - size: Number of results (default: 20)

        For Tuniu:
        - city_name: City name (required)
        - check_in: Check-in date YYYY-MM-DD (required)
        - check_out: Check-out date YYYY-MM-DD (required)
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)
        - keyword: Hotel name or brand keyword
        - page_num: Page number (default: 1)
        - query_id: Query ID for pagination (required for pages > 1)

    Returns:
        JSON response with hotel list
    """
    try:
        data = _parse_json_body()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # --- Unified search mode (v3.0): destination parameter ---
        destination = data.get('destination', '').strip()
        if destination:
            return _unified_search(data, destination)

        # --- Legacy single-provider mode (backward compatible) ---
        provider_name = data.get('provider', current_app.config.get('DEFAULT_PROVIDER', 'tuniu'))

        # Get provider
        try:
            provider = get_provider(provider_name)
        except HotelProviderError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        # Build search parameters based on provider
        llm_min_star = None

        if provider_name == 'tuniu':
            # Validate Tuniu required fields
            required = ['city_name', 'check_in', 'check_out']
            for field in required:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400

            search_params = {
                'city_name': data['city_name'],
                'check_in': data['check_in'],
                'check_out': data['check_out'],
                'adult_count': data.get('adult_count', 2),
                'child_count': data.get('child_count', 0),
                'keyword': data.get('keyword'),
                'page_num': data.get('page_num', 1),
                'query_id': data.get('query_id')
            }
        else:
            # RollingGo
            required = ['place', 'place_type']
            for field in required:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400

            # When landmark + city are both provided, use LLM to determine optimal params
            place_val = data['place']
            place_type_val = data['place_type']
            query_val = data.get('query') or data.get('place')

            if data.get('city_name') and place_val != data['city_name']:
                from app.services.intent_parser import get_intent_parser
                parser = get_intent_parser()
                intent = parser.parse(f"{data['city_name']}{place_val}")
                if intent:
                    place_val = f"{intent.get('city', data['city_name'])}{intent.get('place', place_val)}"
                    place_type_val = intent.get('placeType', '详细地址')
                    query_val = place_val
                    llm_min_star = intent.get('minStar')
                    if intent.get('maxPrice') and not data.get('max_price'):
                        data['max_price'] = intent['maxPrice']

            search_params = {
                'query': query_val,
                'place': place_val,
                'place_type': place_type_val,
                'check_in_date': data.get('check_in_date'),
                'stay_nights': data.get('stay_nights'),
                'adult_count': data.get('adult_count', 2),
                'child_count': data.get('child_count', 0),
                'child_ages': data.get('child_ages'),
                'star_ratings': data.get('star_ratings'),
                'max_price': data.get('max_price'),
                'distance': data.get('distance'),
                'required_tags': data.get('required_tags', []),
                'preferred_tags': data.get('preferred_tags', []),
                'size': data.get('size', current_app.config.get('RESULTS_PER_PAGE', 20)),
                'country_code': data.get('country_code')
            }

        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}

        # Check cache
        cache = get_cache_service()
        cache_key = generate_cache_key(f'search:{provider_name}', search_params)

        if current_app.config.get('CACHE_ENABLED', True):
            cached = cache.get_cache(cache_key)
            if cached:
                return jsonify({
                    'success': True,
                    'data': cached,
                    'cached': True
                })

        # Execute search
        result = provider.search_hotels(**search_params)

        # Post-filter: RollingGo API ignores star_ratings, filter locally
        min_star = data.get('min_star') or data.get('minStar') or llm_min_star
        if provider_name == 'rollinggo' and min_star:
            try:
                min_star_f = float(min_star)
                hotels = result.get('hotels', [])
                result['hotels'] = [h for h in hotels
                                    if (h.get('star_rating') or 0) >= min_star_f]
            except (ValueError, TypeError):
                pass
            except (ValueError, TypeError):
                pass

        # RollingGo fallback: landmark not in API → geocode + distance sort
        fallback_from = None
        if (provider_name == 'rollinggo'
                and not result.get('hotels')
                and data.get('city_name')
                and data.get('place') != data.get('city_name')):
            landmark = data.get('place', '')
            city = data.get('city_name', '')
            logger.info(f"RollingGo: 0 results for '{landmark}', "
                        f"geocoding + city search with '{city}'")
            fallback_from = landmark

            # 1. Geocode the landmark
            coords = _geocode(f'{landmark} {city}')

            # 2. Search hotels in the city
            city_params = {**search_params}
            city_params['place'] = city
            city_params['place_type'] = '城市'
            city_params['query'] = city
            result = provider.search_hotels(**city_params)

            # 3. If geocoding succeeded, calculate real distances and re-sort
            if coords:
                landmark_lat, landmark_lon = coords
                logger.info(f"Geocoded '{landmark}' → ({landmark_lat}, {landmark_lon})")
                for hotel in result.get('hotels', []):
                    h_lat = hotel.get('latitude')
                    h_lon = hotel.get('longitude')
                    if h_lat and h_lon:
                        try:
                            hotel['distance'] = round(_haversine(
                                landmark_lat, landmark_lon, float(h_lat), float(h_lon)
                            ))
                        except (ValueError, TypeError):
                            pass
                # Re-sort by distance (hotels without coords go to end)
                result['hotels'] = sorted(
                    result.get('hotels', []),
                    key=lambda h: h.get('distance') if h.get('distance') is not None else float('inf')
                )

        # Build response data
        response_data = {
            'hotels': result.get('hotels', []),
            'total': result.get('total', 0),
            'provider': provider_name,
            'supports_booking': provider.supports_booking,
            'supports_pagination': provider.supports_pagination
        }

        if fallback_from:
            response_data['fallback_from'] = fallback_from

        # Add pagination info for Tuniu
        if provider_name == 'tuniu':
            response_data.update({
                'query_id': result.get('query_id'),
                'page_num': result.get('page_num', 1),
                'has_more': result.get('has_more', False)
            })

        # Add legacy fields for backward compatibility
        if provider_name == 'rollinggo':
            response_data.update({
                'query': data.get('query'),
                'place': data.get('place')
            })
        else:
            response_data.update({
                'query': f"Hotels in {data.get('city_name', '')}",
                'place': data.get('city_name', '')
            })

        # Save to cache BEFORE adding is_favorite (avoid cache pollution with per-user data)
        if current_app.config.get('CACHE_ENABLED', True):
            cache.set_cache(
                cache_key,
                response_data,
                current_app.config.get('CACHE_TTL', 3600)
            )

        # Add is_favorite AFTER caching (per-user data, not cacheable)
        for hotel in response_data.get('hotels', []):
            hotel['is_favorite'] = cache.is_favorite(hotel.get('hotel_id', ''))
        cache.add_search_history(
            query=response_data.get('query', ''),
            place=response_data.get('place', ''),
            place_type=data.get('place_type', '城市')
        )

        # Increment search count and add remaining header
        search_user = _check_search_quota()
        response = jsonify({
            'success': True,
            'data': response_data,
            'cached': False
        })

        if search_user and not search_user.is_member:
            from app.routes.membership import _increment_search_count, _get_search_remaining
            _increment_search_count(search_user)
            remaining = _get_search_remaining(search_user)
            response.headers['X-Search-Remaining'] = str(remaining)

        return response

    except HotelProviderError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@search_bp.route('/tags', methods=['GET'])
def get_tags():
    """
    Get available tags for filtering (RollingGo only).

    Returns:
        JSON response with tag list
    """
    try:
        cache = get_cache_service()
        cache_key = 'tags:all'

        # Check cache (cache tags for longer time)
        if current_app.config.get('CACHE_ENABLED', True):
            cached = cache.get_cache(cache_key)
            if cached:
                return jsonify({
                    'success': True,
                    'data': cached,
                    'cached': True
                })

        # Fetch tags from RollingGo
        provider = get_provider('rollinggo')
        tags = provider._service.get_tags()

        response_data = {'tags': tags}

        # Cache for 24 hours
        if current_app.config.get('CACHE_ENABLED', True):
            cache.set_cache(cache_key, response_data, 86400)

        return jsonify({
            'success': True,
            'data': response_data,
            'cached': False
        })

    except HotelProviderError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Get tags error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@search_bp.route('/place-types', methods=['GET'])
def get_place_types():
    """
    Get available place types (RollingGo only).

    Returns:
        JSON response with place type list
    """
    place_types = current_app.config.get('PLACE_TYPES', [
        '景点', '城市', '机场', '火车站', '地铁站', '酒店', '区/县', '详细地址'
    ])

    return jsonify({
        'success': True,
        'data': {'place_types': place_types}
    })


@search_bp.route('/providers', methods=['GET'])
def list_providers():
    """
    Get list of available providers with their capabilities.

    Returns:
        JSON response with provider list
    """
    providers = get_available_providers()

    return jsonify({
        'success': True,
        'data': {
            'providers': providers,
            'default': current_app.config.get('DEFAULT_PROVIDER', 'tuniu')
        }
    })


# ---------------------------------------------------------------------------
# Unified search (v3.0) — destination-based dual-source query
# ---------------------------------------------------------------------------

# Major Chinese cities used to detect domestic destinations
_DOMESTIC_CITIES = {
    '北京', '上海', '广州', '深圳', '杭州', '成都', '南京', '武汉', '西安',
    '重庆', '天津', '苏州', '厦门', '青岛', '大连', '宁波', '无锡', '长沙',
    '郑州', '佛山', '东莞', '沈阳', '哈尔滨', '长春', '济南', '烟台', '福州',
    '合肥', '常州', '南通', '嘉兴', '绍兴', '温州', '南昌', '太原', '石家庄',
    '昆明', '丽江', '桂林', '三亚', '海口', '珠海', '中山', '惠州', '贵阳',
    '南宁', '兰州', '银川', '西宁', '呼和浩特', '乌鲁木齐', '拉萨',
    # Common aliases
    '京城', '魔都', '羊城', '鹏城', '蓉城', '泉城', '春城', '星城',
}

# Regions that are Chinese-speaking but outside mainland
_OUTBOUND_CN = {'香港', '澳门', '台北', '台中', '高雄', '台南', '花莲'}


def _is_domestic(destination: str) -> bool:
    """Check if a destination is likely domestic China."""
    for city in _DOMESTIC_CITIES:
        if city in destination:
            return True
    return False


def _is_outbound_cn(destination: str) -> bool:
    """Check if destination is HK/MO/TW."""
    for place in _OUTBOUND_CN:
        if place in destination:
            return True
    return False


def _extract_city_from_destination(destination: str, intent: dict) -> str:
    """Extract city name from destination for Tuniu query."""
    # Priority: intent_parser result > direct city match > fallback
    if intent and intent.get('city'):
        return intent['city']
    for city in _DOMESTIC_CITIES:
        if city in destination:
            return city
    # Fallback: first 2 Chinese chars
    import re
    m = re.search(r'[\u4e00-\u9fff]{2,4}(?:市|县|区)', destination)
    if m:
        return m.group(0).rstrip('市县区')
    return destination[:2]


def _search_single_provider(provider_name, search_params, timeout=15):
    """Search a single provider with timeout. Returns (provider_name, result_or_error)."""
    try:
        provider = get_provider(provider_name)
        result = provider.search_hotels(**search_params)
        return (provider_name, result)
    except Exception as e:
        logger.warning(f"[Unified] {provider_name} search failed: {e}")
        return (provider_name, None)


def _unified_search(data: dict, destination: str):
    """
    Unified search: destination → auto-route to single/dual source.

    Flow:
    1. Determine domestic/international via city matching
    2. Parse intent via LLM for better RollingGo params
    3. Domestic: parallel query Tuniu + RollingGo → merge
    4. International: RollingGo only
    """
    check_in = data.get('check_in', '')
    check_out = data.get('check_out', '')
    keyword = data.get('keyword', '')
    adult_count = data.get('adult_count', 2)
    child_count = data.get('child_count', 0)

    if not check_in or not check_out:
        return jsonify({
            'success': False,
            'error': 'check_in and check_out are required'
        }), 400

    # Step 1: Determine route
    is_domestic = _is_domestic(destination)
    is_outbound = _is_outbound_cn(destination)
    logger.info(f"[Unified] destination='{destination}', domestic={is_domestic}, outbound={is_outbound}")

    # Step 2: Parse intent for RollingGo params
    intent = None
    try:
        from app.services.intent_parser import get_intent_parser
        parser = get_intent_parser()
        intent = parser.parse(destination)
        if intent:
            # Fix common LLM misclassifications: short destination → likely a city
            if intent.get('placeType') == '详细地址' and len(destination) <= 4:
                intent['placeType'] = '城市'
                logger.info(f"[Unified] Corrected placeType to '城市' for short destination: '{destination}'")
            logger.info(f"[Unified] Intent parsed: {intent}")
    except Exception as e:
        logger.warning(f"[Unified] Intent parsing failed: {e}")

    # Step 3: Check cache
    cache = get_cache_service()
    cache_params = {
        'destination': destination,
        'check_in': check_in,
        'check_out': check_out,
        'adult_count': adult_count,
        'keyword': keyword,
    }
    cache_key = generate_cache_key('search:unified', cache_params)

    if current_app.config.get('CACHE_ENABLED', True):
        cached = cache.get_cache(cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

    # Step 4: Execute search(es)
    tuniu_result = None
    rollinggo_result = None
    warnings = []

    if is_domestic:
        # --- Domestic: dual-source parallel query ---
        city = _extract_city_from_destination(destination, intent)

        tuniu_params = {
            'city_name': city,
            'check_in': check_in,
            'check_out': check_out,
            'adult_count': adult_count,
            'child_count': child_count,
        }
        if keyword:
            tuniu_params['keyword'] = keyword

        # RollingGo params from intent (use 'or' to handle empty string)
        place = (intent.get('place') or destination) if intent else destination
        place_type = (intent.get('placeType') or '城市') if intent else '城市'
        rollinggo_params = {
            'query': f"{place} {keyword}" if keyword else place,
            'place': place,
            'place_type': place_type,
            'check_in_date': check_in,
            'stay_nights': data.get('stay_nights', 1),
            'adult_count': adult_count,
            'child_count': child_count,
            'size': 20,
        }
        if intent and intent.get('maxPrice'):
            rollinggo_params['max_price'] = intent['maxPrice']

        logger.info(f"[Unified] Domestic dual-source: Tuniu city={city}, RollingGo place={place}")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(_search_single_provider, 'tuniu', tuniu_params): 'tuniu',
                executor.submit(_search_single_provider, 'rollinggo', rollinggo_params): 'rollinggo',
            }
            try:
                for future in as_completed(futures, timeout=25):
                    provider_name = futures[future]
                    try:
                        _, result = future.result()
                        if result is not None:
                            if provider_name == 'tuniu':
                                tuniu_result = result
                            else:
                                rollinggo_result = result
                        else:
                            warnings.append(f'{provider_name} search returned no results')
                    except Exception as e:
                        warnings.append(f'{provider_name} search error: {str(e)}')
            except TimeoutError:
                # One or both providers timed out — use whatever we got
                unfinished = [futures[f] for f in futures if not f.done()]
                warnings.append(f'Provider(s) timed out: {", ".join(unfinished)}')
                logger.warning("[Unified] Timeout waiting for providers: %s", unfinished)

        # Merge results
        from app.services.search_merger import SearchMerger
        merger = SearchMerger()

        # TuniuProvider.search_hotels() already returns normalized data
        tuniu_hotels = tuniu_result.get('hotels', []) if tuniu_result else []
        for h in tuniu_hotels:
            h['provider'] = 'tuniu'
        # RollingGoProvider.search_hotels() also returns normalized data
        rg_hotels = rollinggo_result.get('hotels', []) if rollinggo_result else []
        for h in rg_hotels:
            h['provider'] = 'rollinggo'

        merged = merger.merge(tuniu_hotels, rg_hotels)

        response_data = {
            'hotels': merged['hotels'],
            'total': merged['total'],
            'provider': 'auto',
            'merged': True,
            'sources': merged['sources'],
            'supports_booking': True,
            'query': f"Hotels near {destination}",
            'place': destination,
        }
        if warnings:
            response_data['warnings'] = warnings

    elif is_outbound:
        # --- HK/MO/TW: RollingGo only (no Tuniu coverage) ---
        place = (intent.get('place') or destination) if intent else destination
        place_type = (intent.get('placeType') or '城市') if intent else '城市'
        try:
            provider = get_provider('rollinggo')
            rollinggo_result = provider.search_hotels(
                query=keyword or place,
                place=place,
                place_type=place_type,
                check_in_date=check_in,
                stay_nights=data.get('stay_nights', 1),
                adult_count=adult_count,
                child_count=child_count,
                size=20,
            )
            hotels = rollinggo_result.get('hotels', [])
            for h in hotels:
                h['provider'] = 'rollinggo'

            response_data = {
                'hotels': hotels,
                'total': rollinggo_result.get('total', len(hotels)),
                'provider': 'rollinggo',
                'merged': False,
                'supports_booking': False,
                'query': f"Hotels in {destination}",
                'place': destination,
            }
        except Exception as e:
            logger.error(f"[Unified] RollingGo search for outbound failed: {e}")
            response_data = {
                'hotels': [], 'total': 0, 'provider': 'rollinggo',
                'merged': False, 'error': str(e),
                'query': f"Hotels in {destination}", 'place': destination,
            }

    else:
        # --- International: RollingGo only ---
        place = (intent.get('place') or destination) if intent else destination
        place_type = (intent.get('placeType') or '城市') if intent else '城市'
        try:
            provider = get_provider('rollinggo')
            rollinggo_result = provider.search_hotels(
                query=keyword or place,
                place=place,
                place_type=place_type,
                check_in_date=check_in,
                stay_nights=data.get('stay_nights', 1),
                adult_count=adult_count,
                child_count=child_count,
                size=20,
            )
            hotels = rollinggo_result.get('hotels', [])
            for h in hotels:
                h['provider'] = 'rollinggo'

            response_data = {
                'hotels': hotels,
                'total': rollinggo_result.get('total', len(hotels)),
                'provider': 'rollinggo',
                'merged': False,
                'supports_booking': False,
                'query': f"Hotels in {destination}",
                'place': destination,
            }
        except Exception as e:
            logger.error(f"[Unified] RollingGo search for international failed: {e}")
            response_data = {
                'hotels': [], 'total': 0, 'provider': 'rollinggo',
                'merged': False, 'error': str(e),
                'query': f"Hotels in {destination}", 'place': destination,
            }

    # Step 5: Cache + is_favorite
    if current_app.config.get('CACHE_ENABLED', True):
        cache.set_cache(cache_key, response_data, current_app.config.get('CACHE_TTL', 3600))

    for hotel in response_data.get('hotels', []):
        hotel['is_favorite'] = cache.is_favorite(hotel.get('hotel_id', ''))

    cache.add_search_history(
        query=response_data.get('query', ''),
        place=destination,
        place_type='城市'
    )

    # Search quota
    search_user = _check_search_quota()
    resp = jsonify({'success': True, 'data': response_data, 'cached': False})

    if search_user and not search_user.is_member:
        from app.routes.membership import _increment_search_count, _get_search_remaining
        _increment_search_count(search_user)
        remaining = _get_search_remaining(search_user)
        resp.headers['X-Search-Remaining'] = str(remaining)

    return resp
