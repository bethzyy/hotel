"""
Payment service abstraction layer
Unified interface for multiple payment providers (WeChat Pay, Alipay, Stripe)
"""
import logging
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.models.database import db, User, Subscription

logger = logging.getLogger(__name__)

# Plan definitions (amount in cents)
PLANS = {
    'monthly': {'name': '月度会员', 'amount': 1990, 'days': 30},
    'yearly': {'name': '年度会员', 'amount': 19900, 'days': 365},
}


class PaymentService:
    """Unified payment service."""

    def create_order(self, user_id, plan, payment_provider):
        """
        Create a payment order.

        Returns dict with payment parameters for the frontend.
        """
        if plan not in PLANS:
            raise ValueError(f'Invalid plan: {plan}')

        plan_info = PLANS[plan]
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('User not found')

        try:
            # Create subscription record
            subscription = Subscription(
                user_id=user_id,
                plan=plan,
                amount=plan_info['amount'],
                currency='CNY',
                status='pending',
                payment_provider=payment_provider,
            )
            db.session.add(subscription)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"[Payment] Create order DB error: {e}")
            raise

        # Delegate to specific provider
        if payment_provider == 'wechat':
            return self._create_wechat_order(subscription, plan_info)
        elif payment_provider == 'alipay':
            return self._create_alipay_order(subscription, plan_info)
        else:
            raise ValueError(f'Unsupported payment provider: {payment_provider}')

    def handle_callback(self, payment_provider, raw_data):
        """
        Process payment callback from payment provider.

        Returns True if callback is valid and processed.
        """
        if payment_provider == 'wechat':
            return self._handle_wechat_callback(raw_data)
        elif payment_provider == 'alipay':
            return self._handle_alipay_callback(raw_data)
        else:
            logger.error(f"Unknown payment provider: {payment_provider}")
            return False

    def get_plans(self):
        """Get available subscription plans."""
        return [
            {
                'id': key,
                'name': info['name'],
                'price': info['amount'] / 100,  # Convert to yuan
                'currency': 'CNY',
                'days': info['days'],
                'features': [
                    '无限搜索次数',
                    '价格变动提醒',
                    '历史价格分析',
                    '优先客服支持',
                ],
            }
            for key, info in PLANS.items()
        ]

    def _create_wechat_order(self, subscription, plan_info):
        """Create WeChat Pay order. Placeholder for actual WeChat Pay integration."""
        # TODO: Integrate with WeChat Pay V3 API
        # For now, return a simulated response
        logger.info(f"[Payment] WeChat Pay order created: subscription={subscription.id}")
        return {
            'subscription_id': subscription.id,
            'payment_provider': 'wechat',
            'payment_url': f'/api/payment/mock/wechat/{subscription.id}',
            'qr_code_url': f'weixin://wxpay/bizpayurl?pr={subscription.id}',
        }

    def _create_alipay_order(self, subscription, plan_info):
        """Create Alipay order. Placeholder for actual Alipay integration."""
        # TODO: Integrate with Alipay SDK
        logger.info(f"[Payment] Alipay order created: subscription={subscription.id}")
        return {
            'subscription_id': subscription.id,
            'payment_provider': 'alipay',
            'payment_url': f'/api/payment/mock/alipay/{subscription.id}',
        }

    def _handle_wechat_callback(self, raw_data):
        """Handle WeChat Pay callback. Placeholder."""
        # TODO: Verify signature, update subscription status
        subscription_id = raw_data.get('subscription_id')
        if not subscription_id:
            return False
        return self._activate_subscription(subscription_id, 'wechat', raw_data.get('trade_no'))

    def _handle_alipay_callback(self, raw_data):
        """Handle Alipay callback. Placeholder."""
        # TODO: Verify signature, update subscription status
        subscription_id = raw_data.get('subscription_id')
        if not subscription_id:
            return False
        return self._activate_subscription(subscription_id, 'alipay', raw_data.get('trade_no'))

    def _activate_subscription(self, subscription_id, provider, trade_no):
        """Activate a subscription and update user membership."""
        subscription = db.session.get(Subscription, subscription_id)
        if not subscription:
            logger.error(f"[Payment] Subscription not found: {subscription_id}")
            return False

        # Idempotency check
        if subscription.status == 'active':
            logger.info(f"[Payment] Subscription already active: {subscription_id}")
            return True

        if subscription.status != 'pending':
            logger.error(f"[Payment] Subscription in invalid state: {subscription.status}")
            return False

        # Update subscription
        plan_info = PLANS[subscription.plan]
        now = datetime.now(timezone.utc)
        subscription.status = 'active'
        subscription.payment_trade_no = trade_no
        subscription.started_at = now
        subscription.expires_at = now + timedelta(days=plan_info['days'])

        # Update user membership
        user = db.session.get(User, subscription.user_id)
        if user:
            # If user already has active membership, extend it
            # Handle both timezone-aware and naive datetimes (SQLite stores naive)
            existing_expires = user.membership_expires_at
            if existing_expires and existing_expires.tzinfo is None:
                now_for_compare = now.replace(tzinfo=None)
            else:
                now_for_compare = now
            if user.is_member and existing_expires and existing_expires > now_for_compare:
                new_expires = user.membership_expires_at + timedelta(days=plan_info['days'])
            else:
                new_expires = now + timedelta(days=plan_info['days'])

            user.membership_tier = 'premium'
            user.membership_expires_at = new_expires

        db.session.commit()
        logger.info(f"[Payment] Subscription activated: user={subscription.user_id} plan={subscription.plan}")
        return True


# Singleton
payment_service = PaymentService()
