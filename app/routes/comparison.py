"""
Price Comparison API routes
Compare hotel prices across multiple providers
"""
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.hotel_provider import get_provider, HotelProviderError
from app.services.hotel_matcher import HotelMatcher
from app.services.serper import SerperService
from app.services.tavily import TavilyService
from app.services.currency import convert_to_cny
from app.utils import get_cache_service, generate_cache_key

logger = logging.getLogger(__name__)

comparison_bp = Blueprint('comparison', __name__)

# Create matcher instance
hotel_matcher = HotelMatcher()


@comparison_bp.route('/compare/<provider>/<hotel_id>', methods=['GET'])
def compare_hotel_prices(provider, hotel_id):
    """
    Compare hotel prices across all available providers.

    URL Parameters:
        - provider: Source provider name ('rollinggo' or 'tuniu')
        - hotel_id: Hotel ID from source provider

    Query Parameters:
        - check_in: Check-in date YYYY-MM-DD (required)
        - check_out: Check-out date YYYY-MM-DD (required)
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)
        - hotel_name: Hotel name (optional, improves matching)
        - hotel_address: Hotel address (optional, improves matching)
        - hotel_lat: Hotel latitude (optional, improves matching)
        - hotel_lng: Hotel longitude (optional, improves matching)

    Returns:
        JSON response with comparison results:
        {
            "success": true,
            "data": {
                "source": {
                    "provider": "tuniu",
                    "hotel_id": "xxx",
                    "name": "xxx酒店",
                    "price": 680,
                    "currency": "CNY",
                    "url": "..."
                },
                "comparisons": [
                    {
                        "provider": "rollinggo",
                        "hotel_id": "yyy",
                        "name": "xxx酒店",
                        "price": 720,
                        "currency": "CNY",
                        "url": "...",
                        "match_confidence": 0.92,
                        "match_type": "name+location"
                    }
                ],
                "best_price": {
                    "provider": "tuniu",
                    "price": 680,
                    "save": 40,
                    "url": "..."
                }
            }
        }
    """
    try:
        # Get required parameters
        check_in = request.args.get('check_in') or request.args.get('check_in_date')
        check_out = request.args.get('check_out') or request.args.get('check_out_date')

        logger.info(f"[Comparison] Starting comparison for provider={provider}, hotel_id={hotel_id}")
        logger.debug(f"[Comparison] Request params: check_in={check_in}, check_out={check_out}")
        logger.debug(f"[Comparison] Request params: check_in={check_in}, check_out={check_out}, "
                    f"hotel_name={request.args.get('hotel_name')}, hotel_address={request.args.get('hotel_address')}")

        if not check_in or not check_out:
            return jsonify({
                'success': False,
                'error': 'check_in and check_out are required'
            }), 400

        # Calculate stay nights
        from datetime import datetime
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            stay_nights = (check_out_date - check_in_date).days
            if stay_nights < 1:
                stay_nights = 1
        except ValueError:
            stay_nights = 1

        # Get hotel info from query params (passed from frontend)
        hotel_name = request.args.get('hotel_name', '')
        hotel_address = request.args.get('hotel_address', '')
        hotel_lat = request.args.get('hotel_lat', type=float)
        hotel_lng = request.args.get('hotel_lng', type=float)

        # Build cache key
        cache_params = {
            'provider': provider,
            'hotel_id': hotel_id,
            'check_in': check_in,
            'check_out': check_out,
            'hotel_name': hotel_name
        }
        cache_key = generate_cache_key('compare', cache_params)

        # Check cache (shorter TTL for price comparison: 30 minutes)
        cache = get_cache_service()
        COMPARISON_CACHE_TTL = 1800  # 30 minutes

        if current_app.config.get('CACHE_ENABLED', True):
            cached = cache.get_cache(cache_key)
            if cached:
                return jsonify({
                    'success': True,
                    'data': cached,
                    'cached': True
                })

        # Get source hotel info first
        source_hotel = None
        source_provider = None

        try:
            source_provider = get_provider(provider)

            # Build detail params
            if provider == 'tuniu':
                detail_params = {
                    'hotel_id': hotel_id,
                    'check_in': check_in,
                    'check_out': check_out,
                    'adult_count': request.args.get('adult_count', 2, type=int),
                    'child_count': request.args.get('child_count', 0, type=int)
                }
            else:
                detail_params = {
                    'hotel_id': hotel_id,
                    'check_in_date': check_in,
                    'check_out_date': check_out,
                    'adult_count': request.args.get('adult_count', 2, type=int),
                    'child_count': request.args.get('child_count', 0, type=int)
                }

            source_hotel = source_provider.get_hotel_detail(**detail_params)

        except HotelProviderError as e:
            logger.warning(f"Failed to get source hotel detail: {e}")
            # Use query params as fallback
            source_hotel = {
                'hotel_id': hotel_id,
                'name': hotel_name,
                'address': hotel_address,
                'latitude': hotel_lat,
                'longitude': hotel_lng
            }

        # Enrich source hotel with search params
        source_hotel['check_in'] = check_in
        source_hotel['check_out'] = check_out
        source_hotel['stay_nights'] = stay_nights
        source_hotel['adult_count'] = request.args.get('adult_count', 2, type=int)
        source_hotel['child_count'] = request.args.get('child_count', 0, type=int)

        # Get source price (lowest room plan price)
        source_price = None
        source_currency = 'CNY'
        source_url = None

        if source_hotel.get('room_plans'):
            available_plans = [p for p in source_hotel['room_plans'] if p.get('available', True)]
            if available_plans:
                min_plan = min(available_plans, key=lambda p: p.get('price_per_night') or p.get('price') or float('inf'))
                source_price = min_plan.get('price_per_night') or min_plan.get('price')
                source_currency = min_plan.get('currency', 'CNY')

        # Also check price_per_night from hotel data
        if source_price is None:
            source_price = source_hotel.get('price_per_night')
            source_currency = source_hotel.get('currency', 'CNY')

        # Get booking URL
        source_url = source_hotel.get('booking_url')

        # Build source result
        source_result = {
            'provider': provider,
            'hotel_id': hotel_id,
            'name': source_hotel.get('name', hotel_name),
            'address': source_hotel.get('address', hotel_address),
            'price': source_price,
            'currency': source_currency,
            'url': source_url,
            'supports_booking': source_provider.supports_booking if source_provider else False
        }

        # Compare with other providers
        comparisons = []
        available_providers = ['rollinggo', 'tuniu']
        other_providers = [p for p in available_providers if p != provider]

        # Use ThreadPoolExecutor for parallel queries
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_provider = {}

            for target_provider in other_providers:
                future = executor.submit(
                    search_provider_for_comparison,
                    target_provider,
                    source_hotel,
                    check_in,
                    check_out,
                    stay_nights
                )
                future_to_provider[future] = target_provider

            for future in as_completed(future_to_provider, timeout=30):
                target_provider = future_to_provider[future]
                try:
                    matches = future.result()
                    logger.info(f"[Comparison] Got {len(matches)} matches from {target_provider}")
                    for match in matches[:1]:  # Only take best match
                        # Get best price from matched hotel
                        match_price = match.get('price_per_night')
                        match_currency = match.get('currency', 'CNY')
                        match_url = match.get('booking_url')

                        # Get price from room plans if available
                        if match.get('room_plans'):
                            available_plans = [p for p in match['room_plans'] if p.get('available', True)]
                            if available_plans:
                                min_plan = min(available_plans, key=lambda p: p.get('price_per_night') or p.get('price') or float('inf'))
                                match_price = min_plan.get('price_per_night') or min_plan.get('price')
                                match_currency = min_plan.get('currency', match_currency)

                        comparisons.append({
                            'provider': target_provider,
                            'hotel_id': match.get('hotel_id'),
                            'name': match.get('name'),
                            'address': match.get('address'),
                            'price': match_price,
                            'currency': match_currency,
                            'price_cny': convert_to_cny(match_price, match_currency),
                            'url': match_url,
                            'match_confidence': match.get('match_confidence'),
                            'name_similarity': match.get('name_similarity'),
                            'location_match': match.get('location_match'),
                            'distance_meters': match.get('distance_meters')
                        })
                except Exception as e:
                    logger.error(f"Error comparing with {target_provider}: {e}")

        # Calculate best price
        best_price = None
        all_prices = []

        if source_price:
            all_prices.append({
                'provider': provider,
                'price': source_price,
                'currency': source_currency,
                'url': source_url
            })

        for comp in comparisons:
            if comp.get('price'):
                all_prices.append({
                    'provider': comp['provider'],
                    'price': comp['price'],
                    'currency': comp['currency'],
                    'url': comp['url']
                })

        if all_prices:
            # Find minimum price
            best = min(all_prices, key=lambda x: x['price'])
            # Calculate savings compared to highest price
            highest = max(all_prices, key=lambda x: x['price'])
            save = highest['price'] - best['price'] if len(all_prices) > 1 else 0

            best_price = {
                'provider': best['provider'],
                'price': best['price'],
                'currency': best['currency'],
                'url': best['url'],
                'save': save if save > 0 else None
            }

        # === Tavily external platform search ===
        external_results = []
        tavily_enabled = current_app.config.get('TAVILY_ENABLED', False)
        tavily_api_key = current_app.config.get('TAVILY_API_KEY', '')
        tavily_timeout = current_app.config.get('TAVILY_TIMEOUT', 15)

        # Detailed config logging
        logger.info("=" * 60)
        logger.info("[Comparison] TAVILY CONFIGURATION CHECK")
        logger.info(f"[Comparison]   TAVILY_ENABLED: {tavily_enabled}")
        logger.info(f"[Comparison]   TAVILY_API_KEY: {'SET (' + tavily_api_key[:8] + '...)' if tavily_api_key else 'NOT SET'}")
        logger.info(f"[Comparison]   TAVILY_TIMEOUT: {tavily_timeout}s")
        logger.info(f"[Comparison]   Will call Tavily: {tavily_enabled and bool(tavily_api_key)}")
        logger.info("=" * 60)

        if tavily_enabled and tavily_api_key:
            try:
                tavily = TavilyService(api_key=tavily_api_key, timeout=tavily_timeout)

                # Extract city from address
                city = hotel_matcher._extract_city(source_hotel.get('address', hotel_address))
                hotel_name_for_search = source_hotel.get('name', hotel_name)

                logger.info(f"[Comparison] TAVILY SEARCH PARAMETERS:")
                logger.info(f"[Comparison]   hotel_name: {hotel_name_for_search}")
                logger.info(f"[Comparison]   city: {city or 'NOT EXTRACTED'}")
                logger.info(f"[Comparison]   address: {source_hotel.get('address', hotel_address)}")
                logger.info(f"[Comparison]   check_in: {check_in}")
                logger.info(f"[Comparison]   check_out: {check_out}")
                logger.info(f"[Comparison]   adult_count: {source_hotel.get('adult_count', 2)}")

                tavily_data = tavily.search_hotel_prices(
                    hotel_name=hotel_name_for_search,
                    city=city or '',
                    check_in=check_in,
                    check_out=check_out,
                    adult_count=source_hotel.get('adult_count', 2)
                )

                logger.info(f"[Comparison] TAVILY RAW RESPONSE:")
                logger.info(f"[Comparison]   total_found: {tavily_data.get('total_found', 0)}")
                logger.info(f"[Comparison]   query: {tavily_data.get('query', 'N/A')}")
                logger.info(f"[Comparison]   error: {tavily_data.get('error', 'None')}")

                # Log each result
                for i, r in enumerate(tavily_data.get('results', [])):
                    logger.info(f"[Comparison]   Result #{i+1}: {r.get('platform_name')} - "
                               f"price={r.get('price')}{r.get('currency')} - url={r.get('url', '')[:50]}...")

                external_results = TavilyService.normalize_for_comparison(tavily_data)
                logger.info(f"[Comparison] NORMALIZED: {len(external_results)} external platform results")

                # Log normalized results summary
                for ext in external_results:
                    price_str = f"{ext.get('price')}{ext.get('currency')}" if ext.get('price') else "No price"
                    logger.info(f"[Comparison]   External: {ext.get('platform_name')} = {price_str}")

            except Exception as e:
                logger.error(f"[Comparison] ✗ Tavily search failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            # Fallback to Serper if Tavily is not configured
            logger.info("[Comparison] Tavily not configured, checking Serper fallback...")
            serper_enabled = current_app.config.get('SERPER_ENABLED', False)
            serper_api_key = current_app.config.get('SERPER_API_KEY', '')
            serper_timeout = current_app.config.get('SERPER_TIMEOUT', 10)

            logger.info("[Comparison] SERPER CONFIGURATION:")
            logger.info(f"[Comparison]   SERPER_ENABLED: {serper_enabled}")
            logger.info(f"[Comparison]   SERPER_API_KEY: {'SET (' + serper_api_key[:8] + '...)' if serper_api_key else 'NOT SET'}")
            logger.info(f"[Comparison]   SERPER_TIMEOUT: {serper_timeout}s")

            if serper_enabled and serper_api_key:
                try:
                    serper = SerperService(api_key=serper_api_key, timeout=serper_timeout)

                    # Extract city from address
                    city = hotel_matcher._extract_city(source_hotel.get('address', hotel_address))

                    hotel_name_for_search = source_hotel.get('name', hotel_name)
                    logger.info(f"[Comparison] SERPER SEARCH PARAMETERS:")
                    logger.info(f"[Comparison]   hotel_name: {hotel_name_for_search}")
                    logger.info(f"[Comparison]   city: {city or 'NOT EXTRACTED'}")

                    serper_data = serper.search_hotel_prices(
                        hotel_name=hotel_name_for_search,
                        city=city or '',
                        check_in=check_in,
                        check_out=check_out,
                        adult_count=source_hotel.get('adult_count', 2)
                    )

                    logger.info(f"[Comparison] SERPER RAW RESPONSE:")
                    logger.info(f"[Comparison]   total_found: {serper_data.get('total_found', 0)}")
                    for i, r in enumerate(serper_data.get('results', [])):
                        logger.info(f"[Comparison]   Result #{i+1}: {r.get('platform_name')} - "
                                   f"price={r.get('price')}{r.get('currency')}")

                    external_results = SerperService.normalize_for_comparison(serper_data)
                    logger.info(f"[Comparison] NORMALIZED: {len(external_results)} external platform results from Serper")

                except Exception as e:
                    logger.error(f"[Comparison] ✗ Serper search failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning("[Comparison] Neither Tavily nor Serper is configured for external price search")

        # Add CNY conversion to external results
        for ext in external_results:
            ext['price_cny'] = convert_to_cny(ext.get('price'), ext.get('currency', 'USD'))

        # Build response
        response_data = {
            'source': source_result,
            'comparisons': comparisons,
            'external_prices': external_results,
            'best_price': best_price
        }

        # Final summary logging
        logger.info("=" * 60)
        logger.info("[Comparison] FINAL RESULTS SUMMARY")
        logger.info(f"[Comparison]   Source: {source_result['provider']} - "
                   f"price={source_result.get('price')}{source_result.get('currency')}")
        logger.info(f"[Comparison]   Comparisons: {len(comparisons)} providers")
        for comp in comparisons:
            logger.info(f"[Comparison]     - {comp.get('provider')}: {comp.get('price')}{comp.get('currency')}")
        logger.info(f"[Comparison]   External Prices: {len(external_results)} platforms")
        for ext in external_results:
            price_str = f"{ext.get('price')}{ext.get('currency')}" if ext.get('price') else "No price"
            logger.info(f"[Comparison]     - {ext.get('platform_name')}: {price_str}")
        logger.info(f"[Comparison]   Best Price: {best_price.get('price') if best_price else 'N/A'}")
        logger.info("=" * 60)

        # Save to cache (use shorter TTL if no external prices found)
        if current_app.config.get('CACHE_ENABLED', True):
            # If external search returned no results or all prices are None, use shorter cache
            has_valid_prices = any(
                ext.get('price') is not None
                for ext in external_results
            )
            cache_ttl = COMPARISON_CACHE_TTL if has_valid_prices else 300  # 5 min for no-price results
            logger.info(f"[Comparison] Caching result with TTL={cache_ttl}s (has_valid_prices={has_valid_prices})")
            cache.set_cache(cache_key, response_data, cache_ttl)

        return jsonify({
            'success': True,
            'data': response_data,
            'cached': False
        })

    except Exception as e:
        logger.error(f"Price comparison error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred during price comparison'
        }), 500


def search_provider_for_comparison(
    target_provider: str,
    source_hotel: dict,
    check_in: str,
    check_out: str,
    stay_nights: int
) -> list:
    """
    Search for matching hotels in a target provider.

    Args:
        target_provider: Provider to search in
        source_hotel: Source hotel info
        check_in: Check-in date
        check_out: Check-out date
        stay_nights: Number of nights

    Returns:
        List of matched hotels
    """
    try:
        provider = get_provider(target_provider)
        hotel_name = source_hotel.get('name', '')
        hotel_address = source_hotel.get('address', '')

        logger.info(f"[Comparison] Searching {target_provider} for hotel: {hotel_name}")
        logger.debug(f"[Comparison] Source hotel data: name={hotel_name}, address={hotel_address}, "
                    f"lat={source_hotel.get('latitude')}, lng={source_hotel.get('longitude')}")

        if not hotel_name:
            logger.warning(f"[Comparison] No hotel name provided, skipping {target_provider}")
            return []

        # Build search params based on provider
        if target_provider == 'tuniu':
            # Extract city from address
            city = hotel_matcher._extract_city(hotel_address)
            if not city:
                logger.warning(f"[Comparison] Could not extract city from address: {hotel_address}")
                return []

            search_params = {
                'city_name': city,
                'check_in': check_in,
                'check_out': check_out,
                'keyword': hotel_name,
                'adult_count': source_hotel.get('adult_count', 2),
                'child_count': source_hotel.get('child_count', 0)
            }
            logger.info(f"[Comparison] Tuniu search params: city={city}, keyword={hotel_name}")
        else:
            # RollingGo
            search_params = {
                'query': hotel_name,
                'place': hotel_address or hotel_name,
                'place_type': '酒店',
                'check_in_date': check_in,
                'stay_nights': stay_nights,
                'adult_count': source_hotel.get('adult_count', 2),
                'size': 10
            }
            logger.info(f"[Comparison] RollingGo search params: query={hotel_name}, place={hotel_address or hotel_name}")

        # Execute search
        result = provider.search_hotels(**search_params)
        hotels = result.get('hotels', [])
        logger.info(f"[Comparison] Found {len(hotels)} hotels from {target_provider}")

        if not hotels:
            logger.warning(f"[Comparison] No hotels found from {target_provider}")
            return []

        # Match hotels
        matched = hotel_matcher.match_hotels(source_hotel, hotels)
        logger.info(f"[Comparison] Matched {len(matched)} hotels from {target_provider}")

        # Log match details
        for i, m in enumerate(matched[:3]):
            logger.debug(f"[Comparison] Match {i+1}: {m.get('name')} - "
                        f"confidence={m.get('match_confidence', 0):.2f}, "
                        f"name_sim={m.get('name_similarity', 0):.2f}, "
                        f"location_match={m.get('location_match')}, "
                        f"distance={m.get('distance_meters')}m")

        # For best matches, get detailed info with prices
        detailed_matches = []
        for match in matched[:2]:  # Only top 2 matches
            try:
                if target_provider == 'tuniu':
                    detail_params = {
                        'hotel_id': match['hotel_id'],
                        'check_in': check_in,
                        'check_out': check_out,
                        'adult_count': source_hotel.get('adult_count', 2),
                        'child_count': source_hotel.get('child_count', 0)
                    }
                else:
                    detail_params = {
                        'hotel_id': match['hotel_id'],
                        'check_in_date': check_in,
                        'check_out_date': check_out,
                        'adult_count': source_hotel.get('adult_count', 2)
                    }

                detail = provider.get_hotel_detail(**detail_params)
                match.update(detail)
                detailed_matches.append(match)
                logger.debug(f"[Comparison] Got detail for match: {match.get('name')}")

            except Exception as e:
                logger.warning(f"[Comparison] Failed to get detail for match {match.get('name')}: {e}")
                detailed_matches.append(match)  # Use search result as fallback

        return detailed_matches

    except HotelProviderError as e:
        logger.error(f"[Comparison] Provider error for {target_provider}: {e}")
        return []
    except Exception as e:
        logger.error(f"[Comparison] Search error for {target_provider}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


@comparison_bp.route('/compare/batch', methods=['POST'])
def batch_compare_hotels():
    """
    Batch compare hotel prices across all available providers.

    Used for search results page to show multi-platform prices.

    Request body:
        - source_provider: Source provider name ('rollinggo' or 'tuniu')
        - check_in: Check-in date YYYY-MM-DD (required)
        - check_out: Check-out date YYYY-MM-DD (required)
        - hotels: List of hotels to compare, each with:
            - hotel_id: Hotel ID
            - name: Hotel name
            - address: Hotel address
            - latitude: Hotel latitude (optional)
            - longitude: Hotel longitude (optional)
            - price_per_night: Source price (optional)
            - currency: Currency code (optional)

    Returns:
        JSON response with comparison results for each hotel:
        {
            "success": true,
            "data": {
                "hotel_id_1": {
                    "source": {...},
                    "comparisons": [...],
                    "best_price": {...}
                },
                ...
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        source_provider = data.get('source_provider', 'rollinggo')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        hotels = data.get('hotels', [])

        if not check_in or not check_out:
            return jsonify({
                'success': False,
                'error': 'check_in and check_out are required'
            }), 400

        if not hotels:
            return jsonify({
                'success': True,
                'data': {}
            })

        # Calculate stay nights
        from datetime import datetime
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            stay_nights = (check_out_date - check_in_date).days
            if stay_nights < 1:
                stay_nights = 1
        except ValueError:
            stay_nights = 1

        # Build cache key
        cache_params = {
            'provider': source_provider,
            'check_in': check_in,
            'check_out': check_out,
            'hotel_ids': sorted([h.get('hotel_id', '') for h in hotels])
        }
        cache_key = generate_cache_key('batch_compare', cache_params)

        # Check cache
        cache = get_cache_service()
        COMPARISON_CACHE_TTL = 1800  # 30 minutes

        if current_app.config.get('CACHE_ENABLED', True):
            cached = cache.get_cache(cache_key)
            if cached:
                return jsonify({
                    'success': True,
                    'data': cached,
                    'cached': True
                })

        # Get other providers to compare
        available_providers = ['rollinggo', 'tuniu']
        other_providers = [p for p in available_providers if p != source_provider]

        # Results dictionary
        results = {}

        # Use ThreadPoolExecutor for parallel queries
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_hotel = {}

            for hotel in hotels:
                hotel_id = hotel.get('hotel_id')
                if not hotel_id:
                    continue

                # Build source result
                source_result = {
                    'provider': source_provider,
                    'hotel_id': hotel_id,
                    'name': hotel.get('name', ''),
                    'price': hotel.get('price_per_night'),
                    'currency': hotel.get('currency', 'CNY'),
                    'url': hotel.get('booking_url')
                }

                results[hotel_id] = {
                    'source': source_result,
                    'comparisons': [],
                    'best_price': None
                }

                # Enrich hotel with search params
                hotel['check_in'] = check_in
                hotel['check_out'] = check_out
                hotel['stay_nights'] = stay_nights

                # Submit search for each other provider
                for target_provider in other_providers:
                    future = executor.submit(
                        search_provider_for_comparison,
                        target_provider,
                        hotel,
                        check_in,
                        check_out,
                        stay_nights
                    )
                    future_to_hotel[future] = (hotel_id, target_provider)

            # Collect results
            for future in as_completed(future_to_hotel, timeout=45):
                hotel_id, target_provider = future_to_hotel[future]
                try:
                    matches = future.result()
                    if matches and hotel_id in results:
                        # Get best match
                        best_match = matches[0]

                        # Get price from match
                        match_price = best_match.get('price_per_night')
                        match_currency = best_match.get('currency', 'CNY')
                        match_url = best_match.get('booking_url')

                        # Get price from room plans if available
                        if best_match.get('room_plans'):
                            available_plans = [p for p in best_match['room_plans'] if p.get('available', True)]
                            if available_plans:
                                min_plan = min(available_plans, key=lambda p: p.get('price_per_night') or p.get('price') or float('inf'))
                                match_price = min_plan.get('price_per_night') or min_plan.get('price')
                                match_currency = min_plan.get('currency', match_currency)

                        results[hotel_id]['comparisons'].append({
                            'provider': target_provider,
                            'hotel_id': best_match.get('hotel_id'),
                            'name': best_match.get('name'),
                            'price': match_price,
                            'currency': match_currency,
                            'url': match_url,
                            'match_confidence': best_match.get('match_confidence'),
                            'name_similarity': best_match.get('name_similarity')
                        })
                except Exception as e:
                    logger.error(f"Error comparing hotel {hotel_id} with {target_provider}: {e}")

        # Calculate best price for each hotel
        for hotel_id, result in results.items():
            all_prices = []

            source_price = result['source'].get('price')
            if source_price:
                all_prices.append({
                    'provider': result['source']['provider'],
                    'price': source_price,
                    'currency': result['source'].get('currency', 'CNY'),
                    'url': result['source'].get('url')
                })

            for comp in result['comparisons']:
                if comp.get('price'):
                    all_prices.append({
                        'provider': comp['provider'],
                        'price': comp['price'],
                        'currency': comp.get('currency', 'CNY'),
                        'url': comp.get('url')
                    })

            if all_prices:
                # Find minimum price
                best = min(all_prices, key=lambda x: x['price'])
                # Calculate savings compared to highest price
                highest = max(all_prices, key=lambda x: x['price'])
                save = highest['price'] - best['price'] if len(all_prices) > 1 else 0

                result['best_price'] = {
                    'provider': best['provider'],
                    'price': best['price'],
                    'currency': best.get('currency', 'CNY'),
                    'url': best.get('url'),
                    'save': save if save > 0 else None
                }

        # Save to cache
        if current_app.config.get('CACHE_ENABLED', True):
            cache.set_cache(cache_key, results, COMPARISON_CACHE_TTL)

        return jsonify({
            'success': True,
            'data': results,
            'cached': False
        })

    except Exception as e:
        import traceback
        logger.error(f"Batch price comparison error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred during batch price comparison: {str(e)}'
        }), 500


@comparison_bp.route('/compare/status', methods=['GET'])
def get_comparison_status():
    """
    Get comparison feature status and available providers.

    Returns:
        JSON response with comparison status
    """
    providers = []
    try:
        from app.services.hotel_provider import get_available_providers
        providers = get_available_providers()
    except Exception:
        providers = [
            {'id': 'rollinggo', 'name': 'RollingGo'},
            {'id': 'tuniu', 'name': '途牛'}
        ]

    return jsonify({
        'success': True,
        'data': {
            'enabled': True,
            'providers': providers,
            'cache_ttl_minutes': 30
        }
    })


@comparison_bp.route('/compare/test-serper', methods=['GET'])
def test_serper():
    """
    Test Serper API connectivity and functionality.
    Only available in DEBUG mode.
    """
    if not current_app.config.get('DEBUG', False):
        return jsonify({'error': 'Not found'}), 404

    import requests
    from datetime import datetime, timedelta

    # Get test parameters
    hotel_name = request.args.get('hotel_name', '北京王府井希尔顿酒店')
    city = request.args.get('city', '北京')

    # Default dates: tomorrow and day after
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = datetime.now() + timedelta(days=2)
    check_in = request.args.get('check_in', tomorrow.strftime('%Y-%m-%d'))
    check_out = request.args.get('check_out', day_after.strftime('%Y-%m-%d'))

    # Get config
    serper_enabled = current_app.config.get('SERPER_ENABLED', False)
    serper_api_key = current_app.config.get('SERPER_API_KEY', '')
    serper_timeout = current_app.config.get('SERPER_TIMEOUT', 10)

    logger.info(f"[Test-Serper] Testing with: hotel={hotel_name}, city={city}, "
               f"dates={check_in} to {check_out}")

    # Check configuration
    config_status = {
        'enabled': serper_enabled,
        'has_api_key': bool(serper_api_key),
        'api_key_prefix': serper_api_key[:8] + '...' if serper_api_key else None,
        'timeout': serper_timeout
    }

    if not serper_enabled:
        return jsonify({
            'success': False,
            'error': 'Serper is disabled in config (SERPER_ENABLED=False)',
            'config': config_status
        })

    if not serper_api_key:
        return jsonify({
            'success': False,
            'error': 'Serper API key not configured (SERPER_API_KEY is empty)',
            'config': config_status
        })

    # Test direct API call
    try:
        # Build query
        query = f'{hotel_name} {city} booking price'

        headers = {
            'X-API-KEY': serper_api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'gl': 'cn',
            'hl': 'zh-cn',
            'num': 10
        }

        logger.info(f"[Test-Serper] Calling API: {SerperService.SERPER_API_URL}")
        logger.info(f"[Test-Serper] Query: {query}")

        start_time = datetime.now()
        response = requests.post(
            SerperService.SERPER_API_URL,
            headers=headers,
            json=payload,
            timeout=serper_timeout
        )
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"[Test-Serper] Response: status={response.status_code}, "
                   f"time={elapsed_ms:.0f}ms")

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Serper API returned {response.status_code}',
                'status_code': response.status_code,
                'response_text': response.text[:1000],
                'config': config_status,
                'request': {
                    'query': query,
                    'elapsed_ms': elapsed_ms
                }
            })

        # Parse response
        data = response.json()
        organic_results = data.get('organic', [])

        # Process results
        processed_results = []
        platforms_found = set()

        for item in organic_results:
            url = item.get('link', '')

            # Identify platform
            platform_key = None
            for pk, config in SerperService.PLATFORM_CONFIG.items():
                for domain in config['domains']:
                    if domain in url.lower():
                        platform_key = pk
                        platforms_found.add(pk)
                        break
                if platform_key:
                    break

            processed_results.append({
                'title': item.get('title', ''),
                'snippet': item.get('snippet', '')[:200] if item.get('snippet') else '',
                'link': url,
                'platform': platform_key or 'unknown'
            })

        return jsonify({
            'success': True,
            'config': config_status,
            'request': {
                'query': query,
                'elapsed_ms': elapsed_ms
            },
            'response': {
                'status_code': response.status_code,
                'total_organic_results': len(organic_results),
                'platforms_found': list(platforms_found),
                'results': processed_results[:10],  # First 10 results
                'raw_keys': list(data.keys())
            }
        })

    except requests.exceptions.Timeout:
        logger.error(f"[Test-Serper] Timeout after {serper_timeout}s")
        return jsonify({
            'success': False,
            'error': f'Request timeout after {serper_timeout}s',
            'config': config_status
        })
    except requests.exceptions.RequestException as e:
        logger.error(f"[Test-Serper] Request error: {e}")
        return jsonify({
            'success': False,
            'error': f'Request error: {str(e)}',
            'config': config_status
        })
    except Exception as e:
        import traceback
        logger.error(f"[Test-Serper] Unexpected error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'traceback': traceback.format_exc(),
            'config': config_status
        })


@comparison_bp.route('/compare/test-tavily', methods=['GET'])
def test_tavily():
    """
    Test Tavily API connectivity and functionality.
    Only available in DEBUG mode.
    """
    if not current_app.config.get('DEBUG', False):
        return jsonify({'error': 'Not found'}), 404

    import requests
    from datetime import datetime, timedelta

    # Get test parameters
    hotel_name = request.args.get('hotel_name', '杭州武林万怡酒店')
    city = request.args.get('city', '杭州')

    # Default dates: tomorrow and day after
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = datetime.now() + timedelta(days=2)
    check_in = request.args.get('check_in', tomorrow.strftime('%Y-%m-%d'))
    check_out = request.args.get('check_out', day_after.strftime('%Y-%m-%d'))

    # Get config
    tavily_enabled = current_app.config.get('TAVILY_ENABLED', False)
    tavily_api_key = current_app.config.get('TAVILY_API_KEY', '')
    tavily_timeout = current_app.config.get('TAVILY_TIMEOUT', 15)

    logger.info(f"[Test-Tavily] Testing with: hotel={hotel_name}, city={city}, "
               f"dates={check_in} to {check_out}")

    # Check configuration
    config_status = {
        'enabled': tavily_enabled,
        'has_api_key': bool(tavily_api_key),
        'api_key_prefix': tavily_api_key[:8] + '...' if tavily_api_key else None,
        'timeout': tavily_timeout
    }

    if not tavily_enabled:
        return jsonify({
            'success': False,
            'error': 'Tavily is disabled in config (TAVILY_ENABLED=False)',
            'config': config_status
        })

    if not tavily_api_key:
        return jsonify({
            'success': False,
            'error': 'Tavily API key not configured (TAVILY_API_KEY is empty)',
            'config': config_status
        })

    # Test direct API call
    try:
        # Build query
        query = f'{hotel_name} {city} {check_in} {check_out} booking price'
        tavily_url = 'https://api.tavily.com/search'

        headers = {
            'Authorization': f'Bearer {tavily_api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'query': query,
            'search_depth': 'basic',
            'include_domains': [],
            'exclude_domains': [],
            'include_raw_content': False,
            'max_results': 15,
            'include_answer': False
        }

        logger.info(f"[Test-Tavily] Calling API: {tavily_url}")
        logger.info(f"[Test-Tavily] Query: {query}")

        start_time = datetime.now()
        response = requests.post(
            tavily_url,
            headers=headers,
            json=payload,
            timeout=tavily_timeout
        )
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"[Test-Tavily] Response: status={response.status_code}, "
                   f"time={elapsed_ms:.0f}ms")

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Tavily API returned {response.status_code}',
                'status_code': response.status_code,
                'response_text': response.text[:1000],
                'config': config_status,
                'request': {
                    'query': query,
                    'elapsed_ms': elapsed_ms
                }
            })

        # Parse response
        data = response.json()
        results = data.get('results', [])

        # Process results and extract prices
        processed_results = []
        platforms_found = set()

        for item in results:
            url = item.get('url', '')
            title = item.get('title', '')
            content = item.get('content', '')

            # Identify platform
            platform_key = None
            for pk, config in TavilyService.PLATFORM_CONFIG.items():
                for domain in config['domains']:
                    if domain in url.lower():
                        platform_key = pk
                        platforms_found.add(pk)
                        break
                if platform_key:
                    break

            # Extract price
            tavily = TavilyService(api_key=tavily_api_key)

            # DEBUG: Test if _is_price_reasonable exists and works
            has_method = hasattr(tavily, '_is_price_reasonable')
            if has_method:
                test_result = tavily._is_price_reasonable(14, 'USD', 'test')
            else:
                test_result = 'N/A'

            price, currency = tavily._extract_price(content + ' ' + title)

            # Debug: log full content length and price extraction
            full_content = content + ' ' + title
            logger.debug(f"[Test-Tavily] Platform={platform_key}, content_len={len(content)}, "
                        f"title={title[:50]}..., extracted_price={price} {currency}, "
                        f"has_reasonable_method={has_method}, usd14_test={test_result}")

            processed_results.append({
                'title': title,
                'content': content[:500] if content else '',  # Increased for debugging
                'content_full_len': len(content),  # Debug: show full content length
                'url': url,
                'platform': platform_key or 'unknown',
                'platform_name': TavilyService.PLATFORM_CONFIG.get(platform_key, {}).get('name', 'Unknown'),
                'price': price,
                'currency': currency
            })

        # Get normalized results using the full search_hotel_prices flow
        tavily_service = TavilyService(api_key=tavily_api_key)
        tavily_data = tavily_service.search_hotel_prices(
            hotel_name=hotel_name,
            city=city,
            check_in=check_in,
            check_out=check_out
        )
        normalized = TavilyService.normalize_for_comparison(tavily_data)

        # Add CNY conversion to normalized results
        from app.services.currency import convert_to_cny
        for item in normalized:
            item['price_cny'] = convert_to_cny(item.get('price'), item.get('currency', 'USD'))

        return jsonify({
            'success': True,
            'config': config_status,
            'request': {
                'query': query,
                'elapsed_ms': elapsed_ms
            },
            'response': {
                'status_code': response.status_code,
                'total_results': len(results),
                'platforms_found': list(platforms_found),
                'results': processed_results[:10],  # First 10 results
                'normalized': normalized,
                'raw_keys': list(data.keys())
            },
            'prices': normalized  # Add as top-level for easy access
        })

    except requests.exceptions.Timeout:
        logger.error(f"[Test-Tavily] Timeout after {tavily_timeout}s")
        return jsonify({
            'success': False,
            'error': f'Request timeout after {tavily_timeout}s',
            'config': config_status
        })
    except requests.exceptions.RequestException as e:
        logger.error(f"[Test-Tavily] Request error: {e}")
        return jsonify({
            'success': False,
            'error': f'Request error: {str(e)}',
            'config': config_status
        })
    except Exception as e:
        import traceback
        logger.error(f"[Test-Tavily] Unexpected error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'traceback': traceback.format_exc(),
            'config': config_status
        })
