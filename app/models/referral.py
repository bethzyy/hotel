"""
Referral system models for user growth
"""
import string
import random
from datetime import datetime, timezone
from app.models.database import db


class ReferralCode(db.Model):
    """User referral code (one per user)."""
    __tablename__ = 'referral_codes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, unique=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def generate_code():
        """Generate a unique 6-character referral code."""
        chars = string.ascii_uppercase + string.digits
        for _ in range(10):  # Retry up to 10 times
            code = ''.join(random.choices(chars, k=6))
            if not db.session.query(ReferralCode.id).filter_by(code=code).first():
                return code
        raise RuntimeError('Failed to generate unique referral code')


class ReferralRecord(db.Model):
    """Record of a successful referral."""
    __tablename__ = 'referral_records'

    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    reward_type = db.Column(db.String(20), default='membership_days')  # membership_days/coupon
    reward_value = db.Column(db.Integer, default=7)  # 7 days membership
    referrer_rewarded = db.Column(db.Boolean, default=False)
    referred_rewarded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('referrer_id', 'referred_id', name='uq_referrer_referred'),
    )
