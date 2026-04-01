"""
User behavior tracking models for analytics
"""
from datetime import datetime, timezone
from app.models.database import db


class TrackingEvent(db.Model):
    """User behavior tracking event."""
    __tablename__ = 'tracking_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                        nullable=True, index=True)
    device_fingerprint = db.Column(db.String(128), nullable=True, index=True)
    session_id = db.Column(db.String(64), nullable=True, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_data = db.Column(db.Text, nullable=True)  # JSON
    page = db.Column(db.String(200), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        import json
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'event_type': self.event_type,
            'page': self.page,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if self.event_data:
            try:
                data['event_data'] = json.loads(self.event_data)
            except (json.JSONDecodeError, TypeError):
                pass
        return data
