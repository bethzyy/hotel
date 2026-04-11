"""
Coupon API routes
Manage promotional coupons
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.database import db
from app.models.coupon import Coupon, UserCoupon

logger = logging.getLogger(__name__)

coupon_bp = Blueprint('coupon', __name__)


@coupon_bp.route('/coupons/available', methods=['GET'])
def list_available_coupons():
    """List coupons available for claiming."""
    try:
        coupons = db.session.query(Coupon).filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': {
                'coupons': [c.to_dict() for c in coupons if c.is_valid()]
            }
        })
    except Exception as e:
        logger.error(f"List coupons error: {e}")
        return jsonify({'success': False, 'error': '获取优惠券列表失败'}), 500


@coupon_bp.route('/coupons/<int:coupon_id>/claim', methods=['POST'])
@jwt_required()
def claim_coupon(coupon_id):
    """Claim a coupon."""
    try:
        user_id = int(get_jwt_identity())

        coupon = db.session.get(Coupon, coupon_id)
        if not coupon or not coupon.is_valid():
            return jsonify({'success': False, 'error': '优惠券不存在或已失效'}), 404

        # Check if already claimed
        existing = db.session.query(UserCoupon).filter_by(
            user_id=user_id, coupon_id=coupon_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': '已领取该优惠券'}), 400

        user_coupon = UserCoupon(user_id=user_id, coupon_id=coupon_id)
        db.session.add(user_coupon)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '领取成功',
            'data': user_coupon.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Claim coupon error: {e}")
        return jsonify({'success': False, 'error': '领取失败'}), 500


@coupon_bp.route('/coupons/redeem', methods=['POST'])
@jwt_required()
def redeem_coupon():
    """
    Redeem a coupon (apply to payment/subscription).

    Request body:
        - coupon_id: UserCoupon ID
        - subscription_id: Subscription to apply discount to
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        user_coupon_id = (data or {}).get('coupon_id')

        if not user_coupon_id:
            return jsonify({'success': False, 'error': '请选择优惠券'}), 400

        user_coupon = db.session.get(UserCoupon, user_coupon_id)
        if not user_coupon or user_coupon.user_id != user_id:
            return jsonify({'success': False, 'error': '优惠券不存在'}), 404

        if user_coupon.status != 'unused':
            return jsonify({'success': False, 'error': '优惠券已使用或已过期'}), 400

        # Mark as used
        user_coupon.status = 'used'
        user_coupon.used_at = __import__('datetime').datetime.utcnow()

        # Increment coupon usage count
        if user_coupon.coupon:
            user_coupon.coupon.used_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '优惠券使用成功',
            'data': {
                'discount_type': user_coupon.coupon.discount_type if user_coupon.coupon else None,
                'discount_value': user_coupon.coupon.discount_value if user_coupon.coupon else None,
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Redeem coupon error: {e}")
        return jsonify({'success': False, 'error': '使用优惠券失败'}), 500


@coupon_bp.route('/coupons/mine', methods=['GET'])
@jwt_required()
def my_coupons():
    """Get my coupons."""
    try:
        user_id = int(get_jwt_identity())
        status = request.args.get('status', '')

        query = db.session.query(UserCoupon).filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        coupons = query.order_by(UserCoupon.received_at.desc()).limit(50).all()
        return jsonify({
            'success': True,
            'data': {'coupons': [c.to_dict() for c in coupons]}
        })
    except Exception as e:
        logger.error(f"My coupons error: {e}")
        return jsonify({'success': False, 'error': '获取优惠券失败'}), 500
