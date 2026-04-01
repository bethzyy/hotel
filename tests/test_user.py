"""Favorites and search history CRUD tests."""


class TestFavorites:
    def test_add_favorite(self, client, auth_headers):
        resp = client.post('/api/favorites', headers=auth_headers, json={
            'hotel_id': 'hotel_001',
            'provider': 'tuniu',
            'hotel_name': 'Test Hotel',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_add_favorite_missing_hotel_id(self, client, auth_headers):
        resp = client.post('/api/favorites', headers=auth_headers, json={
            'provider': 'tuniu',
        })
        assert resp.status_code == 400

    def test_get_favorites(self, client, auth_headers):
        # Add a favorite first
        client.post('/api/favorites', headers=auth_headers, json={
            'hotel_id': 'hotel_002', 'provider': 'tuniu', 'hotel_name': 'Hotel 2',
        })
        resp = client.get('/api/favorites', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['total'] >= 1

    def test_toggle_favorite_add(self, client, auth_headers):
        resp = client.post('/api/favorites/toggle', headers=auth_headers, json={
            'hotel_id': 'hotel_003', 'provider': 'tuniu', 'hotel_name': 'Hotel 3',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['is_favorite'] is True
        assert data['data']['action'] == 'added'

    def test_toggle_favorite_remove(self, client, auth_headers):
        # Add then remove
        client.post('/api/favorites/toggle', headers=auth_headers, json={
            'hotel_id': 'hotel_004', 'provider': 'tuniu', 'hotel_name': 'Hotel 4',
        })
        resp = client.post('/api/favorites/toggle', headers=auth_headers, json={
            'hotel_id': 'hotel_004', 'provider': 'tuniu', 'hotel_name': 'Hotel 4',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['is_favorite'] is False
        assert data['data']['action'] == 'removed'

    def test_check_favorite(self, client, auth_headers):
        client.post('/api/favorites', headers=auth_headers, json={
            'hotel_id': 'hotel_005', 'provider': 'tuniu',
        })
        resp = client.get('/api/favorites/hotel_005', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['is_favorite'] is True

    def test_check_favorite_not_found(self, client, auth_headers):
        resp = client.get('/api/favorites/hotel_nonexist', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['is_favorite'] is False

    def test_remove_favorite(self, client, auth_headers):
        client.post('/api/favorites', headers=auth_headers, json={
            'hotel_id': 'hotel_006', 'provider': 'tuniu',
        })
        resp = client.delete('/api/favorites/hotel_006', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_remove_favorite_not_found(self, client, auth_headers):
        resp = client.delete('/api/favorites/hotel_nonexist', headers=auth_headers)
        assert resp.status_code == 404

    def test_duplicate_favorite(self, client, auth_headers):
        client.post('/api/favorites', headers=auth_headers, json={
            'hotel_id': 'hotel_007', 'provider': 'tuniu',
        })
        resp = client.post('/api/favorites', headers=auth_headers, json={
            'hotel_id': 'hotel_007', 'provider': 'tuniu',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True  # Already in favorites, not error


class TestSearchHistory:
    def test_add_history(self, client, auth_headers):
        resp = client.post('/api/history', headers=auth_headers, json={
            'query': '上海酒店',
            'place': '上海',
            'place_type': '城市',
            'provider': 'tuniu',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_get_history(self, client, auth_headers):
        client.post('/api/history', headers=auth_headers, json={
            'query': '北京酒店', 'place': '北京', 'place_type': '城市',
        })
        resp = client.get('/api/history', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['total'] >= 1

    def test_clear_history(self, client, auth_headers):
        client.post('/api/history', headers=auth_headers, json={
            'query': '广州酒店', 'place': '广州', 'place_type': '城市',
        })
        resp = client.delete('/api/history', headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_delete_history_item(self, client, auth_headers):
        client.post('/api/history', headers=auth_headers, json={
            'query': '深圳酒店', 'place': '深圳', 'place_type': '城市',
        })
        resp = client.get('/api/history', headers=auth_headers)
        history = resp.get_json()['data']['history']
        if history:
            item_id = history[0]['id']
            resp = client.delete(f'/api/history/{item_id}', headers=auth_headers)
            assert resp.status_code == 200
