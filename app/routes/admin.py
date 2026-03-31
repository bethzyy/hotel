"""
Admin dashboard routes
Basic statistics and click tracking management
"""
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, render_template_string
from sqlalchemy import func
from app.models.database import db, Click

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
