"""
Authentication API routes
Phone number + verification code login, JWT tokens
"""
import hashlib
import os
import time
import logging
from flask import Blueprint, request, jsonify, current_app
from app.extensions import limiter
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from app.models.database import db, User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


# ==================== Verification Code Storage ====================

class InMemoryVerificationStore:
    """Fallback in-memory store (development mode)."""
    def __init__(self):
        self._store = {}

    def set_code(self, phone, code, ttl_seconds):
        self._store[f'code:{phone}'] = {
            'code': code, 'expires': ttl_seconds, 'created_at': time.time()
        }

    def get_code(self, phone):
        return self._store.get(f'code:{phone}')

    def delete_code(self, phone):
        self._store.pop(f'code:{phone}', None)

    def increment_send_count(self, phone):
        key = f'codes_sent:{phone}'
        self._store[key] = self._store.get(key, 0) + 1
        return self._store[key]

    def get_send_count(self, phone):
        return self._store.get(f'codes_sent:{phone}', 0)


class RedisVerificationStore:
    """Redis-backed verification code store (production mode)."""
    def __init__(self, redis_url):
        import redis
        self._redis = redis.from_url(redis_url, decode_responses=True)

    def set_code(self, phone, code, ttl_seconds):
        self._redis.setex(f'verification:code:{phone}', ttl_seconds, code)

    def get_code(self, phone):
        stored = self._redis.get(f'verification:code:{phone}')
        if stored is None:
            return None
        # Redis handles TTL, return compatible format
        return {'code': stored, 'expires': 300, 'created_at': 0}

    def delete_code(self, phone):
        self._redis.delete(f'verification:code:{phone}')

    def increment_send_count(self, phone):
        key = f'verification:codes_sent:{phone}'
        count = self._redis.incr(key)
        if count == 1:
            self._redis.expire(key, 86400)  # Reset after 24 hours
        return count

    def get_send_count(self, phone):
        return int(self._redis.get(f'verification:codes_sent:{phone}') or 0)


# Module-level store (initialized lazily)
_store = None


def _get_store():
    global _store
    if _store is None:
        redis_url = os.environ.get('REDIS_URL', '')
        if redis_url:
            _store = RedisVerificationStore(redis_url)
        else:
            _store = InMemoryVerificationStore()
    return _store


# ==================== Helper Functions ====================

def _get_device_fingerprint():
    """Get or create a device fingerprint from request headers."""
    fp = request.headers.get('X-Device-Fingerprint', '')
    if not fp:
        ua = request.headers.get('User-Agent', '')
        ip = request.remote_addr or ''
        fp = hashlib.sha256(f"{ua}{ip}".encode()).hexdigest()[:32]
    return fp


# ==================== Routes ====================

@auth_bp.route('/auth/send-code', methods=['POST'])
@limiter.limit("5 per minute")
def send_verification_code():
    """
    Send SMS verification code to phone number.

    Request body:
        - phone: Phone number (required, format: 1XXXXXXXXXX)
    """
    data = request.get_json()
    if not data or not data.get('phone'):
        return jsonify({'success': False, 'error': '手机号不能为空'}), 400

    phone = data['phone']
    import re
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({'success': False, 'error': '手机号格式不正确'}), 400

    # Rate limiting: max 5 codes per phone per day
    store = _get_store()
    count = store.get_send_count(phone)
    if count >= 5:
        return jsonify({'success': False, 'error': '今日发送次数已达上限'}), 429

    # Generate 6-digit code
    import random
    code = str(random.randint(100000, 999999))

    # Store code (Redis handles TTL automatically in production)
    store.set_code(phone, code, 300)
    store.increment_send_count(phone)

    if current_app.config.get('DEBUG'):
        logger.info(f"[Auth] Verification code for {phone}: {code}")
        return jsonify({
            'success': True,
            'message': '验证码已发送',
            'code': code  # Only in debug mode!
        })
    else:
        # TODO: Integrate SMS service (e.g., Alibaba Cloud SMS)
        logger.info(f"[Auth] Verification code sent to {phone}")
        return jsonify({'success': True, 'message': '验证码已发送'})


@auth_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Login or register with phone + verification code.

    Request body:
        - phone: Phone number (required)
        - code: Verification code (required)

    Returns JWT access token.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '请求体不能为空'}), 400

    phone = data.get('phone', '')
    code = data.get('code', '')

    if not phone or not code:
        return jsonify({'success': False, 'error': '手机号和验证码不能为空'}), 400

    # Verify code
    store = _get_store()
    stored = store.get_code(phone)
    if not stored or stored['code'] != str(code):
        return jsonify({'success': False, 'error': '验证码错误'}), 401

    # Check expiration (Redis handles TTL automatically; in-memory needs manual check)
    if stored.get('created_at', 0) > 0:
        if time.time() - stored['created_at'] > stored['expires']:
            store.delete_code(phone)
            return jsonify({'success': False, 'error': '验证码已过期'}), 401

    # Clear used code
    store.delete_code(phone)

    # Find or create user
    user = User.query.filter_by(phone=phone).first()
    if not user:
        user = User(phone=phone)
        db.session.add(user)
        db.session.commit()
        logger.info(f"[Auth] New user registered: {phone}")

    # Generate JWT token
    additional_claims = {'phone': phone}
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        'success': True,
        'data': {
            'access_token': access_token,
            'user': user.to_dict()
        }
    })


@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required(optional=True)
def get_current_user():
    """
    Get current user info. Works for both authenticated and anonymous users.

    For anonymous users, returns device fingerprint as identifier.
    """
    user_id = get_jwt_identity()

    if user_id:
        user = db.session.get(User, int(user_id))
        if user:
            from app.routes.membership import _check_membership, _get_search_remaining
            _check_membership(user.id)
            db.session.refresh(user)

            return jsonify({
                'success': True,
                'data': {
                    'authenticated': True,
                    'user': user.to_dict(),
                    'membership': {
                        'tier': user.membership_tier,
                        'expires_at': user.membership_expires_at.isoformat() if user.membership_expires_at else None,
                        'is_member': user.is_member,
                        'search_remaining': _get_search_remaining(user),
                    }
                }
            })

    # Anonymous user
    device_fp = _get_device_fingerprint()
    return jsonify({
        'success': True,
        'data': {
            'authenticated': False,
            'device_fingerprint': device_fp
        }
    })


@auth_bp.route('/auth/anonymous', methods=['POST'])
def anonymous_login():
    """
    Get or create an anonymous session using device fingerprint.

    Returns a device fingerprint that can be used for favorites/history.
    """
    device_fp = _get_device_fingerprint()

    return jsonify({
        'success': True,
        'data': {
            'authenticated': False,
            'device_fingerprint': device_fp
        }
    })
