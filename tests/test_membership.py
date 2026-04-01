"""Membership system tests."""


class TestMembershipInfo:
    def test_free_user_info(self, client, auth_headers):
        resp = client.get('/api/membership/info', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['tier'] == 'free'
        assert data['data']['is_member'] is False
        assert data['data']['search_remaining'] == 10
        assert data['data']['search_limit'] == 10

    def test_membership_requires_auth(self, client):
        resp = client.get('/api/membership/info')
        # No auth header → 401 or 422 depending on JWT config
        assert resp.status_code in (401, 422)


class TestMembershipCheck:
    def test_check_search_allowed(self, client, auth_headers):
        resp = client.post('/api/membership/check', headers=auth_headers, json={'feature': 'search'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['allowed'] is True

    def test_check_price_alert_requires_member(self, client, auth_headers):
        resp = client.post('/api/membership/check', headers=auth_headers, json={'feature': 'price_alert'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['allowed'] is False
        assert data['data']['reason'] == 'membership_required'

    def test_check_anonymous_search(self, client):
        resp = client.post('/api/membership/check', json={'feature': 'search'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['allowed'] is True
        assert data['data']['reason'] == 'anonymous'
