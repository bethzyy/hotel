"""
Click tracking API routes
Records user click-through events for CPS affiliate tracking
"""
import logging
from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.database import db, Click

logger = logging.getLogger(__name__)

click_bp = Blueprint('click', __name__)


def _get_user_id():
    """Extract user_id from JWT token if available."""
    try:
        uid = get_jwt_identity()
        if uid:
            return int(uid)
    except Exception:
        pass
    return None


@click_bp.route('/click/track', methods=['GET'])
@jwt_required(optional=True)
def track_click():
    """
    Track a click-through event and redirect to the target URL.

    Query Parameters:
        - url: Target URL to redirect to (required)
        - hotel_id: Hotel ID (optional)
        - hotel_name: Hotel name (optional)
        - provider: Provider name (optional)
        - source: Source page (optional)

    Records the click in the database, then issues a 302 redirect.
    """
    target_url = request.args.get('url', '')
    if not target_url:
        return jsonify({'error': 'Missing url parameter'}), 400

    # Basic URL validation
    if not target_url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Invalid URL'}), 400

    hotel_id = request.args.get('hotel_id', '')
    hotel_name = request.args.get('hotel_name', '')
    provider = request.args.get('provider', 'unknown')
    source = request.args.get('source', request.referrer or 'direct')
    user_id = _get_user_id()

    # Record the click
    try:
        click = Click(
            user_id=user_id,
            hotel_id=hotel_id,
            hotel_name=hotel_name,
            provider=provider,
            target_url=target_url[:2000],
            source_page=source[:500] if source else None,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.add(click)
        db.session.commit()
        logger.info(f"Click tracked: hotel={hotel_name} provider={provider} user_id={user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to record click: {e}")
        # Don't block the redirect even if tracking fails

    return redirect(target_url, code=302)
