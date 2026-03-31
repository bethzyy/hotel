"""
User-related API routes (favorites and history)
"""
from flask import Blueprint, request, jsonify, current_app
from app.utils import get_cache_service

user_bp = Blueprint('user', __name__)


# ==================== Favorites API ====================

@user_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """
    Get all favorite hotels.

    Returns:
        JSON response with favorites list
    """
    try:
        cache = get_cache_service()
        favorites = cache.get_favorites()

        return jsonify({
            'success': True,
            'data': {
                'favorites': favorites,
                'total': len(favorites)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Get favorites error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@user_bp.route('/favorites', methods=['POST'])
def add_favorite():
    """
    Add hotel to favorites.

    Request body:
        - hotel_id: Hotel ID (required)
        - hotel_data: Hotel data to store (required)

    Returns:
        JSON response with success status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        hotel_id = data.get('hotel_id')
        hotel_data = data.get('hotel_data')

        if not hotel_id or not hotel_data:
            return jsonify({
                'success': False,
                'error': 'hotel_id and hotel_data are required'
            }), 400

        cache = get_cache_service()

        # Check max favorites limit
        max_favorites = current_app.config.get('MAX_FAVORITES', 50)
        current_count = cache.get_favorites_count()
        if current_count >= max_favorites and not cache.is_favorite(hotel_id):
            return jsonify({
                'success': False,
                'error': f'Maximum favorites limit ({max_favorites}) reached'
            }), 400

        success = cache.add_favorite(hotel_id, hotel_data)

        if success:
            return jsonify({
                'success': True,
                'message': 'Hotel added to favorites'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add favorite'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Add favorite error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@user_bp.route('/favorites/<hotel_id>', methods=['DELETE'])
def remove_favorite(hotel_id):
    """
    Remove hotel from favorites.

    URL Parameters:
        - hotel_id: Hotel ID to remove

    Returns:
        JSON response with success status
    """
    try:
        cache = get_cache_service()
        success = cache.remove_favorite(hotel_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Hotel removed from favorites'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Hotel not found in favorites'
            }), 404

    except Exception as e:
        current_app.logger.error(f"Remove favorite error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@user_bp.route('/favorites/<hotel_id>', methods=['GET'])
def check_favorite(hotel_id):
    """
    Check if hotel is in favorites.

    URL Parameters:
        - hotel_id: Hotel ID to check

    Returns:
        JSON response with favorite status
    """
    try:
        cache = get_cache_service()
        is_favorite = cache.is_favorite(hotel_id)

        return jsonify({
            'success': True,
            'data': {
                'hotel_id': hotel_id,
                'is_favorite': is_favorite
            }
        })

    except Exception as e:
        current_app.logger.error(f"Check favorite error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@user_bp.route('/favorites/toggle', methods=['POST'])
def toggle_favorite():
    """
    Toggle favorite status for a hotel.

    Request body:
        - hotel_id: Hotel ID (required)
        - hotel_data: Hotel data to store if adding (required when adding)

    Returns:
        JSON response with new favorite status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        hotel_id = data.get('hotel_id')
        if not hotel_id:
            return jsonify({
                'success': False,
                'error': 'hotel_id is required'
            }), 400

        cache = get_cache_service()
        is_favorite = cache.is_favorite(hotel_id)

        if is_favorite:
            # Remove from favorites
            cache.remove_favorite(hotel_id)
            return jsonify({
                'success': True,
                'data': {
                    'hotel_id': hotel_id,
                    'is_favorite': False,
                    'action': 'removed'
                }
            })
        else:
            # Add to favorites
            hotel_data = data.get('hotel_data')
            if not hotel_data:
                return jsonify({
                    'success': False,
                    'error': 'hotel_data is required when adding favorite'
                }), 400

            # Check max favorites limit
            max_favorites = current_app.config.get('MAX_FAVORITES', 50)
            current_count = cache.get_favorites_count()
            if current_count >= max_favorites:
                return jsonify({
                    'success': False,
                    'error': f'Maximum favorites limit ({max_favorites}) reached'
                }), 400

            cache.add_favorite(hotel_id, hotel_data)
            return jsonify({
                'success': True,
                'data': {
                    'hotel_id': hotel_id,
                    'is_favorite': True,
                    'action': 'added'
                }
            })

    except Exception as e:
        current_app.logger.error(f"Toggle favorite error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


# ==================== Search History API ====================

@user_bp.route('/history', methods=['GET'])
def get_search_history():
    """
    Get search history.

    Query Parameters:
        - limit: Maximum number of entries (default: 10)

    Returns:
        JSON response with search history
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, current_app.config.get('MAX_HISTORY', 20))

        cache = get_cache_service()
        history = cache.get_search_history(limit)

        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'total': len(history)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Get search history error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@user_bp.route('/history', methods=['DELETE'])
def clear_search_history():
    """
    Clear all search history.

    Returns:
        JSON response with success status
    """
    try:
        cache = get_cache_service()
        cache.clear_search_history()

        return jsonify({
            'success': True,
            'message': 'Search history cleared'
        })

    except Exception as e:
        current_app.logger.error(f"Clear search history error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500


@user_bp.route('/history/<int:history_id>', methods=['DELETE'])
def delete_search_history_item(history_id):
    """
    Delete specific search history entry.

    URL Parameters:
        - history_id: History entry ID

    Returns:
        JSON response with success status
    """
    try:
        cache = get_cache_service()
        success = cache.delete_search_history(history_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'History entry deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'History entry not found'
            }), 404

    except Exception as e:
        current_app.logger.error(f"Delete search history error: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500
