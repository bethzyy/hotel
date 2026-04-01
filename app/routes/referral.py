"""
Referral reward API routes
Invite friends, earn membership days
"""
import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.models.database import db, User
from app.models.referral import ReferralCode, ReferralRecord

logger = logging.getLogger(__name__)

referral_bp = Blueprint('referral', __name__)

REFERRAL_REWARD_DAYS = 7


def _grant_membership_days(user_id, days):
    """Grant membership days to a user (extend or activate)."""
    user = db.session.get(User, user_id)
    if not user:
        return

    now = datetime.now(timezone.utc)
    if user.is_member and user.membership_expires_at and user.membership_expires_at > now:
        user.membership_expires_at = user.membership_expires_at + timedelta(days=days)
    else:
        user.membership_tier = 'premium'
        user.membership_expires_at = now + timedelta(days=days)

    db.session.commit()
    logger.info(f"[Referral] Granted {days} days membership to user {user_id}")


@referral_bp.route('/referral/code', methods=['GET'])
@jwt_required()
def get_referral_code():
    """Get or create the current user's referral code."""
    user_id = int(get_jwt_identity())

    code = db.session.query(ReferralCode).filter_by(user_id=user_id).first()
    if not code:
        code = ReferralCode(user_id=user_id, code=ReferralCode.generate_code())
        db.session.add(code)
        db.session.commit()

    # Get stats
    total_referrals = db.session.query(func.count(ReferralRecord.id)).filter(
        ReferralRecord.referrer_id == user_id
    ).scalar() or 0

    return jsonify({
        'success': True,
        'data': {
            'code': code.code,
            'total_referrals': total_referrals,
            'reward_days': REFERRAL_REWARD_DAYS,
        }
    })


@referral_bp.route('/referral/apply', methods=['POST'])
@jwt_required()
def apply_referral_code():
    """
    Apply a referral code during registration/login.

    Request body:
        - code: Referral code (required)
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    code_str = (data or {}).get('code', '').strip().upper()

    if not code_str:
        return jsonify({'success': False, 'error': '推荐码不能为空'}), 400

    # Find the referral code
    ref_code = db.session.query(ReferralCode).filter_by(code=code_str).first()
    if not ref_code:
        return jsonify({'success': False, 'error': '推荐码不存在'}), 404

    # Can't refer yourself
    if ref_code.user_id == user_id:
        return jsonify({'success': False, 'error': '不能使用自己的推荐码'}), 400

    # Check if already referred
    existing = db.session.query(ReferralRecord).filter_by(
        referrer_id=ref_code.user_id, referred_id=user_id
    ).first()
    if existing:
        return jsonify({'success': False, 'error': '已经使用过推荐码'}), 400

    # Create referral record
    record = ReferralRecord(
        referrer_id=ref_code.user_id,
        referred_id=user_id,
        reward_type='membership_days',
        reward_value=REFERRAL_REWARD_DAYS,
    )
    db.session.add(record)
    db.session.commit()

    # Grant rewards to both parties
    try:
        _grant_membership_days(user_id, REFERRAL_REWARD_DAYS)
        record.referred_rewarded = True

        _grant_membership_days(ref_code.user_id, REFERRAL_REWARD_DAYS)
        record.referrer_rewarded = True

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Referral] Failed to grant rewards: {e}")

    return jsonify({
        'success': True,
        'message': f'推荐码使用成功，双方各获得 {REFERRAL_REWARD_DAYS} 天会员'
    })


@referral_bp.route('/referral/records', methods=['GET'])
@jwt_required()
def get_referral_records():
    """Get my referral records."""
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 20, type=int)

    records = db.session.query(ReferralRecord).filter(
        ReferralRecord.referrer_id == user_id
    ).order_by(ReferralRecord.created_at.desc()).limit(limit).all()

    return jsonify({
        'success': True,
        'data': {
            'records': [{
                'id': r.id,
                'referred_id': r.referred_id,
                'reward_value': r.reward_value,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            } for r in records]
        }
    })
