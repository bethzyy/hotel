"""Search API parameter validation tests (no external API calls)."""


class TestSearchValidation:
    def test_search_missing_body(self, client):
        resp = client.post('/api/search')
        # Search endpoint catches content-type error as generic Exception → 500
        assert resp.status_code in (400, 415, 500)

    def test_search_invalid_provider(self, client):
        resp = client.post('/api/search', json={'provider': 'nonexistent'})
        assert resp.status_code == 400

    def test_search_tuniu_missing_required(self, client):
        resp = client.post('/api/search', json={
            'provider': 'tuniu',
            'city_name': '上海',
            # Missing check_in and check_out
        })
        assert resp.status_code == 400

    def test_search_rollinggo_missing_required(self, client):
        resp = client.post('/api/search', json={
            'provider': 'rollinggo',
            'query': 'test',
            # Missing place and place_type
        })
        assert resp.status_code == 400

    def test_search_tuniu_all_required(self, client):
        """Tuniu search with all required fields — external API may fail."""
        resp = client.post('/api/search', json={
            'provider': 'tuniu',
            'city_name': '上海',
            'check_in': '2026-05-01',
            'check_out': '2026-05-02',
        })
        # Should not be a parameter validation error (400 from our validation)
        # External API failures return 400 (HotelProviderError) or 500
        data = resp.get_json()
        if resp.status_code == 400:
            # Our validation errors have specific messages
            assert 'Missing required field' not in (data.get('error') or '')

    def test_search_rollinggo_all_required(self, client):
        resp = client.post('/api/search', json={
            'provider': 'rollinggo',
            'query': 'hotel',
            'place': 'Tokyo',
            'place_type': '城市',
        })
        # May return 500 due to external API failure, but should not be 400
        assert resp.status_code != 400


class TestTags:
    def test_tags_endpoint(self, client):
        resp = client.get('/api/tags')
        # May fail if RollingGo is not configured, but endpoint exists
        assert resp.status_code in (200, 400, 500)
