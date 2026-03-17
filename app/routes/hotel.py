"""
Hotel detail API routes
Supports multiple MCP providers (RollingGo, Tuniu)
"""
import hashlib
import json
from flask import Blueprint, request, jsonify, current_app
from app.services.hotel_provider import get_provider, HotelProviderError

hotel_bp = Blueprint('hotel', __name__)


def get_cache_service():
    """Get cache service from app context."""
    return current_app.cache_service


def generate_cache_key(prefix: str, data: dict) -> str:
    """Generate cache key from data."""
    data_str = json.dumps(data, sort_keys=True)
    return f"{prefix}:{hashlib.md5(data_str.encode()).hexdigest()}"


@hotel_bp.route('/hotel/<hotel_id>', methods=['GET'])
def get_hotel_detail(hotel_id):
    """
    Get detailed information for a hotel.

    URL Parameters:
        - hotel_id: Hotel ID (required)

    Query Parameters:
        - provider: Provider name ('rollinggo' or 'tuniu', default: 'tuniu')

        For Tuniu:
        - check_in: Check-in date YYYY-MM-DD (required)
        - check_out: Check-out date YYYY-MM-DD (required)
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)

        For RollingGo:
        - check_in_date: Check-in date YYYY-MM-DD
        - check_out_date: Check-out date YYYY-MM-DD
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)
        - child_ages: Comma-separated list of children's ages
        - room_count: Number of rooms (default: 1)
        - currency: Currency code (default: CNY)

    Returns:
        JSON response with hotel detail
    """
    try:
        provider_name = request.args.get('provider', current_app.config.get('DEFAULT_PROVIDER', 'tuniu'))

        # Get provider
        try:
            provider = get_provider(provider_name)
        except HotelProviderError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        # Build detail parameters based on provider
        if provider_name == 'tuniu':
            check_in = request.args.get('check_in') or request.args.get('check_in_date')
            check_out = request.args.get('check_out') or request.args.get('check_out_date')

            if not check_in or not check_out:
                return jsonify({
                    'success': False,
                    'error': 'check_in and check_out are required for Tuniu provider'
                }), 400

            detail_params = {
                'hotel_id': hotel_id,
                'check_in': check_in,
                'check_out': check_out,
                'adult_count': request.args.get('adult_count', 2, type=int),
                'child_count': request.args.get('child_count', 0, type=int)
            }
        else:
            # RollingGo
            check_in_date = request.args.get('check_in_date') or request.args.get('check_in')
            check_out_date = request.args.get('check_out_date') or request.args.get('check_out')

            # Parse child ages
            child_ages_str = request.args.get('child_ages', '')
            child_ages = []
            if child_ages_str:
                try:
                    child_ages = [int(age.strip()) for age in child_ages_str.split(',')]
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid child_ages format. Use comma-separated integers.'
                    }), 400

            detail_params = {
                'hotel_id': hotel_id,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date,
                'adult_count': request.args.get('adult_count', 2, type=int),
                'child_count': request.args.get('child_count', 0, type=int),
                'child_ages': child_ages if child_ages else None,
                'room_count': request.args.get('room_count', 1, type=int),
                'currency': request.args.get('currency', 'CNY')
            }

        # Remove None values
        detail_params = {k: v for k, v in detail_params.items() if v is not None}

        # Check cache
        cache = get_cache_service()
        cache_key = generate_cache_key(f'detail:{provider_name}', detail_params)

        if current_app.config.get('CACHE_ENABLED', True):
            cached = cache.get_cache(cache_key)
            if cached:
                cached['is_favorite'] = cache.is_favorite(hotel_id)
                return jsonify({
                    'success': True,
                    'data': cached,
                    'cached': True
                })

        # Fetch hotel detail
        result = provider.get_hotel_detail(**detail_params)

        # Check if favorite
        result['is_favorite'] = cache.is_favorite(hotel_id)

        # Add provider info
        result['provider'] = provider_name
        result['supports_booking'] = provider.supports_booking

        # Save to cache
        if current_app.config.get('CACHE_ENABLED', True):
            cache.set_cache(
                cache_key,
                result,
                current_app.config.get('CACHE_TTL', 3600)
            )

        return jsonify({
            'success': True,
            'data': result,
            'cached': False
        })

    except HotelProviderError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Get hotel detail error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@hotel_bp.route('/hotel', methods=['GET'])
def search_hotel_by_name():
    """
    Search for hotel detail by name (RollingGo only, alternative endpoint).

    Query Parameters:
        - name: Hotel name (required)
        - check_in_date: Check-in date YYYY-MM-DD
        - check_out_date: Check-out date YYYY-MM-DD
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)
        - child_ages: Comma-separated list of children's ages
        - room_count: Number of rooms (default: 1)
        - currency: Currency code (default: CNY)

    Returns:
        JSON response with hotel detail
    """
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({
                'success': False,
                'error': 'Hotel name is required'
            }), 400

        # Get RollingGo provider
        provider = get_provider('rollinggo')

        # Get other query parameters
        check_in_date = request.args.get('check_in_date')
        check_out_date = request.args.get('check_out_date')
        adult_count = request.args.get('adult_count', 2, type=int)
        child_count = request.args.get('child_count', 0, type=int)
        room_count = request.args.get('room_count', 1, type=int)
        currency = request.args.get('currency', 'CNY')

        # Parse child ages
        child_ages_str = request.args.get('child_ages', '')
        child_ages = []
        if child_ages_str:
            try:
                child_ages = [int(age.strip()) for age in child_ages_str.split(',')]
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid child_ages format'
                }), 400

        # Fetch hotel detail
        result = provider._service.get_hotel_detail(
            name=name,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adult_count=adult_count,
            child_count=child_count,
            child_ages=child_ages if child_ages else None,
            room_count=room_count,
            currency=currency
        )

        # Normalize hotel detail data
        from app.services.rollinggo import RollingGoService
        normalized = RollingGoService.normalize_hotel_detail(result)
        normalized['provider'] = 'rollinggo'
        normalized['supports_booking'] = False

        return jsonify({
            'success': True,
            'data': normalized
        })

    except HotelProviderError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Search hotel by name error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500
