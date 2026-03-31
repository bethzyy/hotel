"""
Search API routes
Supports multiple MCP providers (RollingGo, Tuniu)
"""
from flask import Blueprint, request, jsonify, current_app
from app.extensions import limiter
from app.services.hotel_provider import get_provider, get_available_providers, HotelProviderError
from app.utils import get_cache_service, generate_cache_key

search_bp = Blueprint('search', __name__)


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
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

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
            required = ['query', 'place', 'place_type']
            for field in required:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400

            search_params = {
                'query': data['query'],
                'place': data['place'],
                'place_type': data['place_type'],
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

        # Check favorites for each hotel
        for hotel in result.get('hotels', []):
            hotel['is_favorite'] = cache.is_favorite(hotel.get('hotel_id', ''))

        response_data = {
            'hotels': result.get('hotels', []),
            'total': result.get('total', 0),
            'provider': provider_name,
            'supports_booking': provider.supports_booking,
            'supports_pagination': provider.supports_pagination
        }

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

        # Save to cache
        if current_app.config.get('CACHE_ENABLED', True):
            cache.set_cache(
                cache_key,
                response_data,
                current_app.config.get('CACHE_TTL', 3600)
            )

        # Save to search history
        cache.add_search_history(
            query=response_data.get('query', ''),
            place=response_data.get('place', ''),
            place_type=data.get('place_type', '城市')
        )

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
        import traceback
        current_app.logger.error(f"Search error: {e}")
        current_app.logger.error(traceback.format_exc())
        error_detail = str(e) if current_app.config.get('DEBUG') else 'Internal server error'
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {error_detail}'
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
