"""
Audit log model for tracking important operations
"""
from datetime import datetime, timezone
from app.models.database import db


class AuditLog(db.Model):
    """Operation audit log."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(100), nullable=True)
    detail = db.Column(db.Text, nullable=True)  # JSON
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    @staticmethod
    def log(action, user_id=None, resource_type=None, resource_id=None, detail=None):
        """Convenience method to create an audit log entry."""
        try:
            from flask import request
            import json

            entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                detail=json.dumps(detail, ensure_ascii=False) if detail else None,
                ip_address=request.remote_addr if request else None,
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            import logging
            logging.getLogger(__name__).error(f"Failed to write audit log: {e}")

    def to_dict(self):
        import json
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if self.detail:
            try:
                data['detail'] = json.loads(self.detail)
            except (json.JSONDecodeError, TypeError):
                pass
        return data
