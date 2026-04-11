"""
Membership API routes
Membership info, plan management, and permission checks
"""
import logging
from datetime import date, datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.database import db, User

logger = logging.getLogger(__name__)

membership_bp = Blueprint('membership', __name__)


def _check_membership(user_id):
    """Check and refresh user membership status if expired."""
    user = db.session.get(User, user_id)
    if not user:
        return None

    # Auto-downgrade expired memberships
    try:
        if user.membership_tier != 'free' and user.membership_expires_at:
            now = datetime.now(timezone.utc)
            expires = user.membership_expires_at
            if expires.tzinfo is None:
                now = now.replace(tzinfo=None)
            if expires <= now:
                user.membership_tier = 'free'
                user.membership_expires_at = None
                db.session.commit()
                logger.info(f"[Membership] Auto-downgraded expired membership: user={user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Membership] Auto-downgrade DB error: user={user_id}: {e}")

    return user


def _get_search_remaining(user):
    """Calculate remaining searches for the user today."""
    if user.is_member:
        return -1  # Unlimited

    free_limit = current_app.config.get('FREE_SEARCH_LIMIT', 10)
    today = date.today()

    # Reset counter if it's a new day
    try:
        if user.last_search_date != today:
            user.search_count_today = 0
            user.last_search_date = today
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Membership] Reset search count DB error: user={user.id}: {e}")

    return max(0, free_limit - user.search_count_today)


def _increment_search_count(user):
    """Increment search count for a free user."""
    if user.is_member:
        return

    today = date.today()
    try:
        if user.last_search_date != today:
            user.search_count_today = 0
            user.last_search_date = today

        user.search_count_today += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Membership] Increment search count DB error: user={user.id}: {e}")


@membership_bp.route('/membership/info', methods=['GET'])
@jwt_required()
def get_membership_info():
    """Get current user's membership info."""
    try:
        user_id = int(get_jwt_identity())
        user = _check_membership(user_id)
        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        remaining = _get_search_remaining(user)

        return jsonify({
            'success': True,
            'data': {
                'tier': user.membership_tier,
                'expires_at': user.membership_expires_at.isoformat() if user.membership_expires_at else None,
                'is_member': user.is_member,
                'search_remaining': remaining,
                'search_limit': -1 if user.is_member else current_app.config.get('FREE_SEARCH_LIMIT', 10),
            }
        })
    except Exception as e:
        logger.error(f"Get membership info error: {e}")
        return jsonify({'success': False, 'error': '获取会员信息失败'}), 500


@membership_bp.route('/membership/check', methods=['POST'])
@jwt_required(optional=True)
def check_permission():
    """
    Check if a feature is available for the current user.

    Request body:
        - feature: Feature name to check (e.g., 'search', 'price_alert', 'compare')
    """
    try:
        data = request.get_json()
        feature = (data or {}).get('feature', 'search')

        user_id = get_jwt_identity()
        if not user_id:
            # Anonymous user
            if feature == 'search':
                return jsonify({'success': True, 'data': {'allowed': True, 'reason': 'anonymous'}})
            return jsonify({'success': True, 'data': {'allowed': False, 'reason': 'login_required'}})

        user = _check_membership(int(user_id))
        if not user:
            return jsonify({'success': True, 'data': {'allowed': False, 'reason': 'user_not_found'}})

        if user.is_member:
            return jsonify({'success': True, 'data': {'allowed': True, 'reason': 'member'}})

        remaining = _get_search_remaining(user)
        if feature == 'search':
            allowed = remaining > 0
            return jsonify({
                'success': True,
                'data': {
                    'allowed': allowed,
                    'reason': 'quota_exceeded' if not allowed else 'free_quota',
                    'remaining': remaining,
                }
            })

        # Other features require membership
        return jsonify({'success': True, 'data': {'allowed': False, 'reason': 'membership_required'}})

    except Exception as e:
        logger.error(f"Check permission error: {e}")
        return jsonify({'success': False, 'error': '检查权限失败'}), 500
