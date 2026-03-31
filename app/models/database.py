"""
SQLAlchemy database models
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    nickname = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic',
                                cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy='dynamic',
                                      cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Favorite(db.Model):
    """User favorite hotels."""
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    # Anonymous favorites (no user) use device_fingerprint
    device_fingerprint = db.Column(db.String(128), nullable=True, index=True)
    hotel_id = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default='unknown')
    hotel_name = db.Column(db.String(200), nullable=True)
    hotel_data = db.Column(db.Text, nullable=True)  # JSON string of hotel snapshot
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'hotel_id', 'provider',
                            name='uq_user_hotel_provider'),
    )

    def to_dict(self):
        import json
        data = {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'provider': self.provider,
            'hotel_name': self.hotel_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_favorite': True
        }
        if self.hotel_data:
            try:
                data.update(json.loads(self.hotel_data))
            except (json.JSONDecodeError, TypeError):
                pass
        return data


class SearchHistory(db.Model):
    """User search history."""
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    device_fingerprint = db.Column(db.String(128), nullable=True, index=True)
    query = db.Column(db.String(500), nullable=False)
    place = db.Column(db.String(200), nullable=False)
    place_type = db.Column(db.String(50), nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'place': self.place,
            'place_type': self.place_type,
            'provider': self.provider,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Click(db.Model):
    """Click tracking for CPS affiliate."""
    __tablename__ = 'clicks'

    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.String(100), nullable=False, index=True)
    hotel_name = db.Column(db.String(200), nullable=True)
    provider = db.Column(db.String(50), nullable=False)
    target_url = db.Column(db.String(2000), nullable=False)
    source_page = db.Column(db.String(500), nullable=True)
    user_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'hotel_name': self.hotel_name,
            'provider': self.provider,
            'target_url': self.target_url,
            'source_page': self.source_page,
            'user_ip': self.user_ip,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
