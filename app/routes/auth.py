"""
Authentication API routes
Phone number + verification code login, JWT tokens
"""
import hashlib
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

# In-memory verification code store (replace with Redis in production)
_verification_codes = {}


def _get_device_fingerprint():
    """Get or create a device fingerprint from request headers."""
    fp = request.headers.get('X-Device-Fingerprint', '')
    if not fp:
        # Generate from user agent + IP
        ua = request.headers.get('User-Agent', '')
        ip = request.remote_addr or ''
        fp = hashlib.sha256(f"{ua}{ip}".encode()).hexdigest()[:32]
    return fp


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
    # Basic phone format validation
    import re
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({'success': False, 'error': '手机号格式不正确'}), 400

    # Rate limiting: max 5 codes per phone per day
    # (In production, use Redis for this)
    key = f'codes_sent:{phone}'
    count = _verification_codes.get(key, 0)
    if count >= 5:
        return jsonify({'success': False, 'error': '今日发送次数已达上限'}), 429

    # Generate 6-digit code
    import random
    import time
    code = str(random.randint(100000, 999999))

    # Store code (in production, send via SMS API)
    _verification_codes[f'code:{phone}'] = {'code': code, 'expires': 300, 'created_at': time.time()}
    _verification_codes[key] = count + 1

    if current_app.config.get('DEBUG'):
        # Dev mode: return code in response for testing
        logger.info(f"[Auth] Verification code for {phone}: {code}")
        return jsonify({
            'success': True,
            'message': '验证码已发送',
            'code': code  # Only in debug mode!
        })
    else:
        # TODO: Integrate SMS service (e.g., Alibaba Cloud SMS)
        # send_sms(phone, f"您的验证码是{code}，5分钟内有效")
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
    stored = _verification_codes.get(f'code:{phone}')
    if not stored or stored['code'] != code:
        return jsonify({'success': False, 'error': '验证码错误'}), 401

    # Check expiration
    if time.time() - stored.get('created_at', 0) > stored['expires']:
        del _verification_codes[f'code:{phone}']
        return jsonify({'success': False, 'error': '验证码已过期'}), 401

    # Clear used code
    del _verification_codes[f'code:{phone}']

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
            # Check and refresh membership status
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

    # Return the fingerprint so frontend can store it
    return jsonify({
        'success': True,
        'data': {
            'authenticated': False,
            'device_fingerprint': device_fp
        }
    })
