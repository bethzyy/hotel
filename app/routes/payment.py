"""
Payment API routes
Payment order creation, callbacks, and status queries
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.database import db, Subscription, User
from app.services.payment import payment_service

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payment/plans', methods=['GET'])
def list_plans():
    """Get available subscription plans."""
    return jsonify({
        'success': True,
        'data': {'plans': payment_service.get_plans()}
    })


@payment_bp.route('/payment/create', methods=['POST'])
@jwt_required()
def create_payment():
    """
    Create a payment order.

    Request body:
        - plan: 'monthly' or 'yearly'
        - payment_provider: 'wechat' or 'alipay'
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400

        plan = data.get('plan', '')
        provider = data.get('payment_provider', '')

        if plan not in ('monthly', 'yearly'):
            return jsonify({'success': False, 'error': '无效的订阅计划'}), 400
        if provider not in ('wechat', 'alipay'):
            return jsonify({'success': False, 'error': '不支持的支付方式'}), 400

        user_id = int(get_jwt_identity())
        result = payment_service.create_order(user_id, plan, provider)

        return jsonify({'success': True, 'data': result})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Create payment error: {e}")
        return jsonify({'success': False, 'error': '创建支付订单失败'}), 500


@payment_bp.route('/payment/wechat/callback', methods=['POST'])
def wechat_callback():
    """WeChat Pay callback endpoint."""
    try:
        data = request.get_json(force=True)
        success = payment_service.handle_callback('wechat', data)
        if success:
            return jsonify({'code': 'SUCCESS', 'message': 'OK'})
        return jsonify({'code': 'FAIL', 'message': 'Invalid callback'}), 400
    except Exception as e:
        logger.error(f"WeChat callback error: {e}")
        return jsonify({'code': 'FAIL', 'message': 'Internal error'}), 500


@payment_bp.route('/payment/alipay/callback', methods=['POST'])
def alipay_callback():
    """Alipay callback endpoint."""
    try:
        data = request.form.to_dict()
        success = payment_service.handle_callback('alipay', data)
        if success:
            return 'success'
        return 'fail', 400
    except Exception as e:
        logger.error(f"Alipay callback error: {e}")
        return 'fail', 500


@payment_bp.route('/payment/status/<int:subscription_id>', methods=['GET'])
@jwt_required()
def payment_status(subscription_id):
    """Get payment/subscription status."""
    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        return jsonify({'success': False, 'error': '订阅记录不存在'}), 404

    # Verify ownership
    user_id = int(get_jwt_identity())
    if subscription.user_id != user_id:
        return jsonify({'success': False, 'error': '无权查看'}), 403

    return jsonify({
        'success': True,
        'data': subscription.to_dict()
    })


@payment_bp.route('/payment/mock/<provider>/<int:subscription_id>', methods=['GET'])
@jwt_required()
def mock_payment(provider, subscription_id):
    """
    Mock payment endpoint for development/testing.
    Simulates a successful payment callback.
    Only available in DEBUG mode.
    """
    if not current_app.config.get('DEBUG'):
        return jsonify({'success': False, 'error': 'Not available in production'}), 403

    subscription = db.session.get(Subscription, subscription_id)
    if not subscription:
        return jsonify({'success': False, 'error': '订阅记录不存在'}), 404

    # Verify ownership
    user_id = int(get_jwt_identity())
    if subscription.user_id != user_id:
        return jsonify({'success': False, 'error': '无权操作'}), 403

    # Simulate successful payment
    mock_data = {
        'subscription_id': subscription_id,
        'trade_no': f'MOCK_{provider}_{subscription_id}_{int(__import__("time").time())}',
    }
    success = payment_service.handle_callback(provider, mock_data)

    if success:
        return jsonify({'success': True, 'message': '模拟支付成功'})
    return jsonify({'success': False, 'error': '模拟支付失败'}), 500
