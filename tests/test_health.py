"""Health check and basic endpoint tests."""


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert data['database'] == 'ok'
        assert 'timestamp' in data


class TestProviders:
    def test_list_providers(self, client):
        resp = client.get('/api/providers')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        providers = data['data']['providers']
        assert len(providers) >= 2

    def test_place_types(self, client):
        resp = client.get('/api/place-types')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        place_types = data['data']['place_types']
        assert '城市' in place_types
        assert '景点' in place_types


class TestRobotsTxt:
    def test_robots_txt(self, client):
        resp = client.get('/robots.txt')
        # robots.txt served from Nuxt dist (SPA static folder) or 404 if not built
        assert resp.status_code in (200, 404)
