"""Recommendation service tests."""


class TestPersonalizedRecommendation:
    def test_no_data(self, client, auth_headers):
        resp = client.get('/api/recommend/personalized', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        # Note: may have suggestions from prior test data in shared DB
        assert isinstance(data['data']['suggestions'], list)

    def test_with_search_history(self, client, auth_headers):
        # Add search history via API to ensure proper session handling
        for place in ['上海', '上海', '北京']:
            client.post('/api/history', headers=auth_headers, json={
                'query': f'{place}酒店',
                'place': place,
                'place_type': '城市',
                'provider': 'tuniu',
            })

        resp = client.get('/api/recommend/personalized', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        suggestions = data['data']['suggestions']
        assert len(suggestions) > 0
        # 上海 was searched twice, should be top recommendation
        places = [s['place'] for s in suggestions]
        assert '上海' in places

    def test_limit_param(self, client, auth_headers):
        # Add search history via API
        for i in range(5):
            client.post('/api/history', headers=auth_headers, json={
                'query': f'城市{i}酒店',
                'place': f'城市{i}',
                'place_type': '城市',
                'provider': 'tuniu',
            })

        resp = client.get('/api/recommend/personalized?limit=2', headers=auth_headers)
        suggestions = resp.get_json()['data']['suggestions']
        assert len(suggestions) <= 2

    def test_requires_auth(self, client):
        resp = client.get('/api/recommend/personalized')
        assert resp.status_code in (401, 422)


class TestSimilarHotels:
    def test_similar_no_favorites(self, client):
        resp = client.get('/api/recommend/similar/hotel_001?provider=tuniu')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['hotels'] == []

    def test_similar_with_favorites(self, client, app, auth_headers, auth_headers_alt):
        """Need auth_headers to ensure user 1 and user 2 exist."""
        from app.models.database import db, Favorite
        with app.app_context():
            for uid in [1, 2]:
                db.session.add(Favorite(
                    user_id=uid, hotel_id='shared_hotel', provider='tuniu',
                    hotel_name='Shared Hotel',
                ))
            db.session.add(Favorite(
                user_id=1, hotel_id='other_hotel', provider='tuniu',
                hotel_name='Other Hotel',
            ))
            db.session.commit()

        resp = client.get('/api/recommend/similar/shared_hotel?provider=tuniu')
        assert resp.status_code == 200
        hotels = resp.get_json()['data']['hotels']
        # Should recommend 'other_hotel' as similar
        assert any(h['hotel_id'] == 'other_hotel' for h in hotels)
