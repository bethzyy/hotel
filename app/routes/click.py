"""
Click tracking API routes
Records user click-through events for CPS affiliate tracking
"""
import logging
from flask import Blueprint, request, jsonify, redirect, current_app
from app.utils import get_cache_service

logger = logging.getLogger(__name__)

click_bp = Blueprint('click', __name__)


@click_bp.route('/click/track', methods=['GET'])
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

    # Record the click
    try:
        cache = get_cache_service()
        cache.record_click(
            hotel_id=hotel_id,
            hotel_name=hotel_name,
            provider=provider,
            target_url=target_url,
            source_page=source,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        logger.info(f"Click tracked: hotel={hotel_name} provider={provider} url={target_url[:100]}")
    except Exception as e:
        logger.error(f"Failed to record click: {e}")
        # Don't block the redirect even if tracking fails

    return redirect(target_url, code=302)
