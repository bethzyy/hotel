"""
Recommendation API routes
Personalized and similar hotel recommendations
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.recommendation import recommendation_service

logger = logging.getLogger(__name__)

recommendation_bp = Blueprint('recommendation', __name__)


@recommendation_bp.route('/recommend/personalized', methods=['GET'])
@jwt_required()
def get_personalized():
    """Get personalized hotel recommendations based on user behavior."""
    try:
        user_id = int(get_jwt_identity())
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 20)

        suggestions = recommendation_service.get_personalized_suggestions(user_id, limit)

        return jsonify({
            'success': True,
            'data': {'suggestions': suggestions}
        })
    except Exception as e:
        logger.error(f"Get personalized recommendations error: {e}")
        return jsonify({'success': False, 'error': '获取推荐失败'}), 500


@recommendation_bp.route('/recommend/similar/<hotel_id>', methods=['GET'])
def get_similar(hotel_id):
    """Get similar hotels based on collaborative filtering."""
    try:
        provider = request.args.get('provider', 'tuniu')
        limit = request.args.get('limit', 5, type=int)
        limit = min(limit, 10)

        similar = recommendation_service.get_similar_hotels(hotel_id, provider, limit)

        return jsonify({
            'success': True,
            'data': {'hotels': similar}
        })
    except Exception as e:
        logger.error(f"Get similar hotels error: {e}")
        return jsonify({'success': False, 'error': '获取推荐失败'}), 500
