"""
Event tracking API routes
Batch event collection for user behavior analytics
"""
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.database import db
from app.models.tracking import TrackingEvent

logger = logging.getLogger(__name__)

tracking_bp = Blueprint('tracking', __name__)


def _get_identity():
    """Get (user_id, device_fingerprint). Reuses user.py pattern."""
    try:
        user_id = get_jwt_identity()
        if user_id:
            return int(user_id), None
    except Exception:
        pass

    fp = request.headers.get('X-Device-Fingerprint', '')
    if not fp:
        ua = request.headers.get('User-Agent', '')
        ip = request.remote_addr or ''
        import hashlib
        fp = hashlib.sha256(f"{ua}{ip}".encode()).hexdigest()[:32]
    return None, fp


@tracking_bp.route('/events/track', methods=['POST'])
@jwt_required(optional=True)
def track_events():
    """
    Batch event tracking endpoint.

    Accepts an array of events:
    [
        {
            "event_type": "search|pageview|view_hotel|compare|click_book|favorite",
            "event_data": { ... },   // optional
            "page": "/results",      // optional
            "timestamp": 1234567890  // optional, client timestamp
        }
    ]
    """
    try:
        data = request.get_json()
        if data is None or not isinstance(data, list):
            return jsonify({'success': False, 'error': 'Expected JSON array of events'}), 400

        if len(data) > 50:
            return jsonify({'success': False, 'error': 'Maximum 50 events per request'}), 400

        user_id, device_fp = _get_identity()
        session_id = request.headers.get('X-Session-ID', '')

        events = []
        for item in data:
            event_type = item.get('event_type', '')
            if not event_type:
                continue

            event = TrackingEvent(
                user_id=user_id,
                device_fingerprint=device_fp if not user_id else None,
                session_id=session_id,
                event_type=event_type[:50],
                event_data=json.dumps(item.get('event_data'), ensure_ascii=False) if item.get('event_data') else None,
                page=item.get('page', '')[:200] or None,
                referrer=request.referrer[:500] if request.referrer else None,
                user_agent=request.headers.get('User-Agent', '')[:500],
                ip_address=request.remote_addr,
            )
            events.append(event)

        if events:
            db.session.add_all(events)
            db.session.commit()

        return jsonify({'success': True, 'data': {'count': len(events)}})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Track events error: {e}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500
