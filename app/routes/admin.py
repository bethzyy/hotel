"""
Admin dashboard routes
Basic statistics and click tracking management
"""
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, render_template_string
from sqlalchemy import func, distinct
from app.models.database import db, Click, User, SearchHistory, Favorite
from app.models.tracking import TrackingEvent

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')


def check_auth(username, password):
    if not ADMIN_PASSWORD:
        return False
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def authenticate():
    return jsonify({'error': 'Authentication required'}), 401, {
        'WWW-Authenticate': 'Basic realm="Admin Dashboard"'
    }


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin/stats')
@requires_auth
def dashboard_stats():
    """Get dashboard statistics."""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    total_clicks = db.session.query(func.count(Click.id)).filter(Click.created_at >= since).scalar() or 0
    unique_hotels = db.session.query(func.count(func.distinct(Click.hotel_id))).filter(Click.created_at >= since).scalar() or 0

    # By provider
    provider_stats = db.session.query(
        Click.provider,
        func.count(Click.id).label('clicks'),
        func.count(func.distinct(Click.hotel_id)).label('unique_hotels'),
        func.min(Click.created_at).label('first_click'),
        func.max(Click.created_at).label('last_click')
    ).filter(Click.created_at >= since).group_by(Click.provider).all()

    return jsonify({
        'success': True,
        'data': {
            'total_clicks': total_clicks,
            'unique_hotels': unique_hotels,
            'by_provider': [{
                'provider': s.provider,
                'clicks': s.clicks,
                'unique_hotels': s.unique_hotels,
                'first_click': s.first_click.isoformat() if s.first_click else None,
                'last_click': s.last_click.isoformat() if s.last_click else None
            } for s in provider_stats]
        }
    })


@admin_bp.route('/admin/clicks')
@requires_auth
def list_clicks():
    """List recent click records."""
    limit = request.args.get('limit', 50, type=int)
    clicks = Click.query.order_by(Click.created_at.desc()).limit(limit).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in clicks]
    })


@admin_bp.route('/admin/')
@requires_auth
def dashboard_page():
    """Simple admin dashboard page."""
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理后台 - 酒店搜索比价</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{background:#f5f5f5} .card{border:none;box-shadow:0 2px 4px rgba(0,0,0,.1)} .stat-value{font-size:2rem;font-weight:700}</style>
</head>
<body>
<nav class="navbar navbar-dark bg-dark"><div class="container"><span class="navbar-brand">管理后台</span></div></nav>
<div class="container mt-4">
    <div class="row g-3 mb-4">
        <div class="col-md-4"><div class="card p-3 text-center"><div class="text-muted">总点击数</div><div class="stat-value" id="total-clicks">-</div></div></div>
        <div class="col-md-4"><div class="card p-3 text-center"><div class="text-muted">覆盖酒店数</div><div class="stat-value" id="unique-hotels">-</div></div></div>
        <div class="col-md-4"><div class="card p-3 text-center"><div class="text-muted">供应商数</div><div class="stat-value" id="provider-count">-</div></div></div>
    </div>
    <div class="card"><div class="card-header d-flex justify-content-between"><h5 class="mb-0">最近点击记录</h5><select id="days-select" class="form-select form-select-sm" style="width:auto"><option value="7">近7天</option><option value="30" selected>近30天</option><option value="90">近90天</option></select></div><div class="card-body p-0"><table class="table table-hover mb-0"><thead><tr><th>时间</th><th>酒店</th><th>供应商</th><th>来源</th><th>IP</th></tr></thead><tbody id="clicks-body"><tr><td colspan="5" class="text-center p-3">加载中...</td></tr></tbody></table></div></div>
</div>
<script>
const API = '/api/admin';
async function loadStats(days) {
    const [statsRes, clicksRes] = await Promise.all([
        fetch(API + '/stats?days=' + days), fetch(API + '/clicks?limit=50')
    ]);
    const stats = (await statsRes.json()).data;
    const clicks = (await clicksRes.json()).data;
    document.getElementById('total-clicks').textContent = stats.total_clicks;
    document.getElementById('unique-hotels').textContent = stats.unique_hotels;
    document.getElementById('provider-count').textContent = stats.by_provider.length;
    const tbody = document.getElementById('clicks-body');
    if (!clicks.length) { tbody.innerHTML = '<tr><td colspan="5" class="text-center p-3">暂无数据</td></tr>'; return; }
    tbody.innerHTML = clicks.map(c => '<tr><td>' + new Date(c.created_at).toLocaleString('zh-CN') + '</td><td>' + (c.hotel_name || c.hotel_id).substring(0, 30) + '</td><td>' + c.provider + '</td><td>' + (c.source_page || '-').substring(0, 20) + '</td><td>' + (c.user_ip || '-') + '</td></tr>').join('');
}
document.getElementById('days-select').addEventListener('change', e => loadStats(e.target.value));
loadStats(30);
</script>
</body></html>'''
    return render_template_string(html)


# ==================== Analytics API ====================

@admin_bp.route('/admin/analytics/overview')
@requires_auth
def analytics_overview():
    """Get analytics overview: DAU, search volume, clicks, favorites."""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    # Total users
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    new_users = db.session.query(func.count(User.id)).filter(User.created_at >= since).scalar() or 0

    # Search events (from tracking)
    search_count = db.session.query(func.count(TrackingEvent.id)).filter(
        TrackingEvent.event_type == 'search',
        TrackingEvent.created_at >= since
    ).scalar() or 0

    # Pageview events
    pageview_count = db.session.query(func.count(TrackingEvent.id)).filter(
        TrackingEvent.event_type == 'pageview',
        TrackingEvent.created_at >= since
    ).scalar() or 0

    # Click throughs
    click_count = db.session.query(func.count(Click.id)).filter(Click.created_at >= since).scalar() or 0

    # Favorites
    fav_count = db.session.query(func.count(Favorite.id)).filter(Favorite.created_at >= since).scalar() or 0

    # DAU (unique users/sessions per day, averaged)
    dau = db.session.query(
        func.count(func.distinct(TrackingEvent.user_id + TrackingEvent.device_fingerprint))
    ).filter(TrackingEvent.created_at >= since).scalar() or 0

    # Daily trend (last 7 days)
    daily_trend = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        day_searches = db.session.query(func.count(TrackingEvent.id)).filter(
            TrackingEvent.event_type == 'search',
            TrackingEvent.created_at >= day_start,
            TrackingEvent.created_at <= day_end
        ).scalar() or 0

        day_clicks = db.session.query(func.count(Click.id)).filter(
            Click.created_at >= day_start,
            Click.created_at <= day_end
        ).scalar() or 0

        daily_trend.append({
            'date': day.isoformat(),
            'searches': day_searches,
            'clicks': day_clicks,
        })

    return jsonify({
        'success': True,
        'data': {
            'total_users': total_users,
            'new_users': new_users,
            'searches': search_count,
            'pageviews': pageview_count,
            'clicks': click_count,
            'favorites': fav_count,
            'dau': dau,
            'daily_trend': daily_trend,
        }
    })


@admin_bp.route('/admin/analytics/funnel')
@requires_auth
def analytics_funnel():
    """Get conversion funnel: search -> view_hotel -> compare -> click_book."""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    event_counts = {}
    for event_type in ['search', 'view_hotel', 'compare', 'click_book', 'favorite']:
        count = db.session.query(func.count(TrackingEvent.id)).filter(
            TrackingEvent.event_type == event_type,
            TrackingEvent.created_at >= since
        ).scalar() or 0
        event_counts[event_type] = count

    total_searches = event_counts.get('search', 1) or 1

    return jsonify({
        'success': True,
        'data': {
            'funnel': [
                {'step': 'search', 'label': '搜索', 'count': event_counts.get('search', 0), 'rate': 100.0},
                {'step': 'view_hotel', 'label': '查看酒店', 'count': event_counts.get('view_hotel', 0),
                 'rate': round(event_counts.get('view_hotel', 0) / total_searches * 100, 1)},
                {'step': 'compare', 'label': '比价', 'count': event_counts.get('compare', 0),
                 'rate': round(event_counts.get('compare', 0) / total_searches * 100, 1)},
                {'step': 'click_book', 'label': '点击预订', 'count': event_counts.get('click_book', 0),
                 'rate': round(event_counts.get('click_book', 0) / total_searches * 100, 1)},
                {'step': 'favorite', 'label': '收藏', 'count': event_counts.get('favorite', 0),
                 'rate': round(event_counts.get('favorite', 0) / total_searches * 100, 1)},
            ]
        }
    })


@admin_bp.route('/admin/analytics/users')
@requires_auth
def analytics_users():
    """Get user analytics: registration rate, activity, top users."""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    total_users = db.session.query(func.count(User.id)).scalar() or 0
    new_users = db.session.query(func.count(User.id)).filter(User.created_at >= since).scalar() or 0

    # Active users (users with tracking events)
    active_users = db.session.query(func.count(distinct(TrackingEvent.user_id))).filter(
        TrackingEvent.user_id.isnot(None),
        TrackingEvent.created_at >= since
    ).scalar() or 0

    # Users with clicks (conversion)
    converting_users = db.session.query(func.count(distinct(Click.user_id))).filter(
        Click.user_id.isnot(None),
        Click.created_at >= since
    ).scalar() or 0

    # Top users by search count
    top_searchers = db.session.query(
        TrackingEvent.user_id,
        func.count(TrackingEvent.id).label('search_count')
    ).filter(
        TrackingEvent.event_type == 'search',
        TrackingEvent.user_id.isnot(None),
        TrackingEvent.created_at >= since
    ).group_by(TrackingEvent.user_id).order_by(func.count(TrackingEvent.id).desc()).limit(10).all()

    # Top users by click count
    top_clickers = db.session.query(
        Click.user_id,
        func.count(Click.id).label('click_count')
    ).filter(
        Click.user_id.isnot(None),
        Click.created_at >= since
    ).group_by(Click.user_id).order_by(func.count(Click.id).desc()).limit(10).all()

    return jsonify({
        'success': True,
        'data': {
            'total_users': total_users,
            'new_users': new_users,
            'active_users': active_users,
            'converting_users': converting_users,
            'conversion_rate': round(converting_users / total_users * 100, 1) if total_users else 0,
            'top_searchers': [{'user_id': u.user_id, 'count': u.search_count} for u in top_searchers],
            'top_clickers': [{'user_id': u.user_id, 'count': u.click_count} for u in top_clickers],
        }
    })
