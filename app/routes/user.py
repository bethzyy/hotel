"""
User-related API routes (favorites and history)
Supports both authenticated users (JWT) and anonymous users (device fingerprint)
"""
import json
import hashlib
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select, delete, func
from app.models.database import db, User, Favorite, SearchHistory

user_bp = Blueprint('user', __name__)


def _get_identity():
    """Get (user_id, device_fingerprint). user_id is None for anonymous users."""
    try:
        user_id = get_jwt_identity()
        if user_id:
            return int(user_id), None
    except Exception:
        pass

    fp = request.headers.get('X-Device-Fingerprint', '')
    if not fp:
        ua = request.headers.get('User-Agent', '')
        ip = request.remote_addr or ''
        fp = hashlib.sha256(f"{ua}{ip}".encode()).hexdigest()[:32]
    return None, fp


# ==================== Favorites API ====================

@user_bp.route('/favorites', methods=['GET'])
@jwt_required(optional=True)
def get_favorites():
    """Get all favorite hotels."""
    try:
        user_id, device_fp = _get_identity()
        stmt = select(Favorite).order_by(Favorite.created_at.desc())
        if user_id:
            stmt = stmt.where(Favorite.user_id == user_id)
        else:
            stmt = stmt.where(Favorite.device_fingerprint == device_fp)
        favorites = [f.to_dict() for f in db.session.execute(stmt).scalars().all()]

        return jsonify({
            'success': True,
            'data': {'favorites': favorites, 'total': len(favorites)}
        })
    except Exception as e:
        current_app.logger.error(f"Get favorites error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/favorites', methods=['POST'])
@jwt_required(optional=True)
def add_favorite():
    """Add hotel to favorites."""
    try:
        data = request.get_json()
        if not data or not data.get('hotel_id'):
            return jsonify({'success': False, 'error': 'hotel_id is required'}), 400

        user_id, device_fp = _get_identity()

        existing = db.session.execute(
            select(Favorite).where(
                (Favorite.user_id == user_id if user_id else Favorite.device_fingerprint == device_fp),
                Favorite.hotel_id == data['hotel_id']
            )
        ).scalars().first()
        if existing:
            return jsonify({'success': True, 'message': 'Already in favorites'})

        max_fav = current_app.config.get('MAX_FAVORITES', 50)
        count = db.session.execute(
            select(func.count()).select_from(Favorite).where(
                Favorite.user_id == user_id if user_id else Favorite.device_fingerprint == device_fp
            )
        ).scalar() or 0
        if count >= max_fav:
            return jsonify({'success': False, 'error': f'最多收藏 {max_fav} 个酒店'}), 400

        fav = Favorite(
            user_id=user_id, device_fingerprint=device_fp,
            hotel_id=data['hotel_id'], provider=data.get('provider', 'unknown'),
            hotel_name=data.get('hotel_name', data.get('name', '')),
            hotel_data=json.dumps(data, ensure_ascii=False)
        )
        db.session.add(fav)
        db.session.commit()
        return jsonify({'success': True, 'message': '已添加收藏'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add favorite error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/favorites/<hotel_id>', methods=['DELETE'])
@jwt_required(optional=True)
def remove_favorite(hotel_id):
    """Remove hotel from favorites."""
    try:
        user_id, device_fp = _get_identity()
        fav = db.session.execute(
            select(Favorite).where(
                (Favorite.user_id == user_id if user_id else Favorite.device_fingerprint == device_fp),
                Favorite.hotel_id == hotel_id
            )
        ).scalars().first()
        if not fav:
            return jsonify({'success': False, 'error': '未收藏该酒店'}), 404
        db.session.delete(fav)
        db.session.commit()
        return jsonify({'success': True, 'message': '已取消收藏'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove favorite error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/favorites/<hotel_id>', methods=['GET'])
@jwt_required(optional=True)
def check_favorite(hotel_id):
    """Check if hotel is in favorites."""
    try:
        user_id, device_fp = _get_identity()
        fav = db.session.execute(
            select(Favorite).where(
                (Favorite.user_id == user_id if user_id else Favorite.device_fingerprint == device_fp),
                Favorite.hotel_id == hotel_id
            )
        ).scalars().first()
        return jsonify({'success': True, 'data': {'hotel_id': hotel_id, 'is_favorite': fav is not None}})
    except Exception as e:
        current_app.logger.error(f"Check favorite error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/favorites/toggle', methods=['POST'])
@jwt_required(optional=True)
def toggle_favorite():
    """Toggle favorite status for a hotel."""
    try:
        data = request.get_json()
        if not data or not data.get('hotel_id'):
            return jsonify({'success': False, 'error': 'hotel_id is required'}), 400

        hotel_id = data['hotel_id']
        user_id, device_fp = _get_identity()
        where_cond = (
            (Favorite.user_id == user_id if user_id else Favorite.device_fingerprint == device_fp),
            Favorite.hotel_id == hotel_id
        )
        fav = db.session.execute(select(Favorite).where(*where_cond)).scalars().first()

        if fav:
            db.session.delete(fav)
            db.session.commit()
            return jsonify({'success': True, 'data': {'hotel_id': hotel_id, 'is_favorite': False, 'action': 'removed'}})
        else:
            max_fav = current_app.config.get('MAX_FAVORITES', 50)
            count = db.session.execute(
                select(func.count()).select_from(Favorite).where(
                    Favorite.user_id == user_id if user_id else Favorite.device_fingerprint == device_fp
                )
            ).scalar() or 0
            if count >= max_fav:
                return jsonify({'success': False, 'error': f'最多收藏 {max_fav} 个酒店'}), 400

            new_fav = Favorite(
                user_id=user_id, device_fingerprint=device_fp,
                hotel_id=hotel_id, provider=data.get('provider', 'unknown'),
                hotel_name=data.get('hotel_name', data.get('name', '')),
                hotel_data=json.dumps(data, ensure_ascii=False)
            )
            db.session.add(new_fav)
            db.session.commit()
            return jsonify({'success': True, 'data': {'hotel_id': hotel_id, 'is_favorite': True, 'action': 'added'}})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle favorite error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


# ==================== Search History API ====================

@user_bp.route('/history', methods=['GET'])
@jwt_required(optional=True)
def get_search_history():
    """Get search history."""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, current_app.config.get('MAX_HISTORY', 20))

        user_id, device_fp = _get_identity()
        stmt = select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(limit)
        if user_id:
            stmt = stmt.where(SearchHistory.user_id == user_id)
        else:
            stmt = stmt.where(SearchHistory.device_fingerprint == device_fp)

        history = [h.to_dict() for h in db.session.execute(stmt).scalars().all()]
        return jsonify({'success': True, 'data': {'history': history, 'total': len(history)}})
    except Exception as e:
        current_app.logger.error(f"Get search history error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/history', methods=['POST'])
@jwt_required(optional=True)
def add_search_history():
    """Add a search to history."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400

        user_id, device_fp = _get_identity()
        history = SearchHistory(
            user_id=user_id, device_fingerprint=device_fp,
            query=data.get('query', ''), place=data.get('place', ''),
            place_type=data.get('place_type'), provider=data.get('provider')
        )
        db.session.add(history)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add search history error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/history', methods=['DELETE'])
@jwt_required(optional=True)
def clear_search_history():
    """Clear all search history."""
    try:
        user_id, device_fp = _get_identity()
        stmt = delete(SearchHistory)
        if user_id:
            stmt = stmt.where(SearchHistory.user_id == user_id)
        else:
            stmt = stmt.where(SearchHistory.device_fingerprint == device_fp)
        db.session.execute(stmt)
        db.session.commit()
        return jsonify({'success': True, 'message': '搜索历史已清空'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Clear search history error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@user_bp.route('/history/<int:history_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_search_history_item(history_id):
    """Delete specific search history entry."""
    try:
        user_id, device_fp = _get_identity()
        item = db.session.get(SearchHistory, history_id)
        if not item:
            return jsonify({'success': False, 'error': '记录不存在'}), 404
        if user_id and item.user_id != user_id:
            return jsonify({'success': False, 'error': '无权操作'}), 403
        if device_fp and item.device_fingerprint != device_fp:
            return jsonify({'success': False, 'error': '无权操作'}), 403
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': '已删除'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete search history error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500
