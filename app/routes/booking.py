"""
Booking API routes
Handles hotel booking flow: prepare, create, and status
"""
from flask import Blueprint, request, jsonify, current_app, render_template
from app.services.hotel_provider import get_provider, HotelProviderError

booking_bp = Blueprint('booking', __name__)


@booking_bp.route('/book/prepare', methods=['POST'])
def prepare_booking():
    """
    Prepare for booking by validating room availability and getting booking parameters.

    Request body:
        - provider: Provider name (default: tuniu)
        - hotel_id: Hotel ID (required)
        - room_id: Room type ID (required)
        - check_in: Check-in date YYYY-MM-DD (required)
        - check_out: Check-out date YYYY-MM-DD (required)
        - adult_count: Number of adults (default: 2)
        - child_count: Number of children (default: 0)

    Returns:
        JSON response with booking preparation info
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate required fields
        required = ['hotel_id', 'check_in', 'check_out']
        for field in required:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        provider_name = data.get('provider', 'tuniu')
        hotel_id = data['hotel_id']
        check_in = data['check_in']
        check_out = data['check_out']

        # Get provider
        try:
            provider = get_provider(provider_name)
        except HotelProviderError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        # Check if provider supports booking
        if not provider.supports_booking:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_name} does not support booking'
            }), 400

        # Get hotel detail to validate room availability
        hotel_detail = provider.get_hotel_detail(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            adult_count=data.get('adult_count', 2),
            child_count=data.get('child_count', 0)
        )

        # Find the requested room
        room_id = data.get('room_id')
        room_plans = hotel_detail.get('room_plans', [])

        if room_id:
            selected_room = next(
                (r for r in room_plans if r.get('room_id') == room_id),
                None
            )
            if not selected_room:
                return jsonify({
                    'success': False,
                    'error': 'Requested room not found or not available'
                }), 404
        else:
            # If no room_id specified, return all available rooms
            selected_room = None

        # Calculate nights
        from datetime import datetime
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        nights = (check_out_date - check_in_date).days

        response_data = {
            'hotel': {
                'hotel_id': hotel_detail.get('hotel_id'),
                'name': hotel_detail.get('name'),
                'address': hotel_detail.get('address'),
                'star_rating': hotel_detail.get('star_rating'),
                'image_url': hotel_detail.get('image_url')
            },
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'adult_count': data.get('adult_count', 2),
            'child_count': data.get('child_count', 0),
            'selected_room': selected_room,
            'available_rooms': room_plans,
            'provider': provider_name,
            'supports_booking': True
        }

        return jsonify({
            'success': True,
            'data': response_data
        })

    except HotelProviderError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Prepare booking error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@booking_bp.route('/book/create', methods=['POST'])
def create_booking():
    """
    Create a hotel booking order.

    Request body:
        - provider: Provider name (default: tuniu)
        - hotel_id: Hotel ID (required)
        - room_id: Room type ID (required)
        - pre_book_param: Pre-booking parameter from detail (required)
        - check_in_date: Check-in date YYYY-MM-DD (required)
        - check_out_date: Check-out date YYYY-MM-DD (required)
        - room_count: Number of rooms (default: 1)
        - room_guests: List of guest info for each room (required)
        - contact_name: Contact person name (required)
        - contact_phone: Contact person phone (required)

    Returns:
        JSON response with order details
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate required fields
        required = ['hotel_id', 'room_id', 'pre_book_param', 'check_in_date',
                    'check_out_date', 'room_guests', 'contact_name', 'contact_phone']
        for field in required:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        provider_name = data.get('provider', 'tuniu')

        # Get provider
        try:
            provider = get_provider(provider_name)
        except HotelProviderError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        # Check if provider supports booking
        if not provider.supports_booking:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_name} does not support booking'
            }), 400

        # Create order
        result = provider.create_order(
            hotel_id=data['hotel_id'],
            room_id=data['room_id'],
            pre_book_param=data['pre_book_param'],
            check_in_date=data['check_in_date'],
            check_out_date=data['check_out_date'],
            room_count=data.get('room_count', 1),
            room_guests=data['room_guests'],
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone']
        )

        return jsonify({
            'success': True,
            'data': result
        })

    except HotelProviderError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Create booking error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@booking_bp.route('/providers', methods=['GET'])
def get_providers():
    """
    Get list of available providers with their capabilities.

    Returns:
        JSON response with provider list
    """
    from app.services.hotel_provider import get_available_providers

    providers = get_available_providers()

    return jsonify({
        'success': True,
        'data': {
            'providers': providers
        }
    })


@booking_bp.route('/booking', methods=['GET'])
def booking_page():
    """Render booking confirmation page."""
    return render_template('booking.html')


@booking_bp.route('/order', methods=['GET'])
def order_page():
    """Render order result page."""
    return render_template('order.html')
