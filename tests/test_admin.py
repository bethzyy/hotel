"""Admin dashboard API tests."""


class TestAdminAuth:
    def test_admin_without_auth(self, client):
        resp = client.get('/api/admin/stats')
        assert resp.status_code == 401

    def test_admin_with_wrong_auth(self, client):
        from base64 import b64encode
        credentials = b64encode(b'admin:wrongpassword').decode()
        resp = client.get('/api/admin/stats', headers={'Authorization': f'Basic {credentials}'})
        assert resp.status_code == 401

    def test_admin_with_correct_auth(self, client, admin_headers):
        resp = client.get('/api/admin/stats', headers=admin_headers)
        assert resp.status_code == 200


class TestAdminStats:
    def test_stats_response(self, client, admin_headers):
        resp = client.get('/api/admin/stats', headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'total_clicks' in data['data']
        assert 'unique_hotels' in data['data']
        assert 'by_provider' in data['data']

    def test_stats_with_days_param(self, client, admin_headers):
        resp = client.get('/api/admin/stats?days=7', headers=admin_headers)
        assert resp.status_code == 200


class TestAdminClicks:
    def test_list_clicks(self, client, admin_headers):
        resp = client.get('/api/admin/clicks', headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_list_clicks_limit(self, client, admin_headers):
        resp = client.get('/api/admin/clicks?limit=5', headers=admin_headers)
        assert resp.status_code == 200


class TestAdminAnalytics:
    def test_analytics_overview(self, client, admin_headers):
        resp = client.get('/api/admin/analytics/overview', headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        overview = data['data']
        assert 'total_users' in overview
        assert 'searches' in overview
        assert 'clicks' in overview
        assert 'dau' in overview
        assert 'daily_trend' in overview

    def test_analytics_funnel(self, client, admin_headers):
        resp = client.get('/api/admin/analytics/funnel', headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        funnel = data['data']['funnel']
        assert len(funnel) >= 5
        # Verify funnel steps
        step_names = [f['step'] for f in funnel]
        assert 'search' in step_names
        assert 'view_hotel' in step_names

    def test_analytics_users(self, client, admin_headers):
        resp = client.get('/api/admin/analytics/users', headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        user_data = data['data']
        assert 'total_users' in user_data
        assert 'active_users' in user_data

    def test_admin_dashboard_page(self, client, admin_headers):
        resp = client.get('/api/admin/', headers=admin_headers)
        assert resp.status_code == 200
        assert b'<html' in resp.data.lower() or b'<!DOCTYPE' in resp.data
