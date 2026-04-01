"""
Coupon system models for promotions
"""
from datetime import datetime, timezone
from app.models.database import db


class Coupon(db.Model):
    """Coupon template."""
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage/fixed_days
    discount_value = db.Column(db.Integer, nullable=False)  # e.g., 20 for 20% or 7 for 7 days
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def is_valid(self):
        """Check if coupon is currently valid."""
        if not self.is_active:
            return False
        now = datetime.now(timezone.utc)
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_valid': self.is_valid(),
        }


class UserCoupon(db.Model):
    """Coupon claimed by a user."""
    __tablename__ = 'user_coupons'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    status = db.Column(db.String(20), default='unused', index=True)  # unused/used/expired
    used_at = db.Column(db.DateTime, nullable=True)
    received_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    coupon = db.relationship('Coupon', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'coupon': self.coupon.to_dict() if self.coupon else None,
            'status': self.status,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
        }
