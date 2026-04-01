"""Event tracking API tests."""


class TestEventTrack:
    def test_track_events_success(self, client):
        events = [
            {'event_type': 'pageview', 'page': '/'},
            {'event_type': 'search', 'event_data': {'provider': 'tuniu', 'place': '上海'}},
        ]
        resp = client.post('/api/events/track', json=events)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['count'] == 2

    def test_track_single_event(self, client):
        resp = client.post('/api/events/track', json=[
            {'event_type': 'view_hotel', 'event_data': {'hotel_id': 'h001'}}
        ])
        assert resp.status_code == 200
        assert resp.get_json()['data']['count'] == 1

    def test_track_empty_events(self, client):
        resp = client.post('/api/events/track', json=[])
        assert resp.status_code == 200
        assert resp.get_json()['data']['count'] == 0

    def test_track_not_array(self, client):
        resp = client.post('/api/events/track', json={'event_type': 'pageview'})
        assert resp.status_code == 400

    def test_track_too_many_events(self, client):
        events = [{'event_type': 'pageview'} for _ in range(51)]
        resp = client.post('/api/events/track', json=events)
        assert resp.status_code == 400

    def test_track_with_auth(self, client, auth_headers, app):
        from app.models.tracking import TrackingEvent
        with app.app_context():
            count_before = TrackingEvent.query.count()
            resp = client.post('/api/events/track', headers=auth_headers, json=[
                {'event_type': 'search', 'event_data': {'place': '北京'}}
            ])
            assert resp.status_code == 200
            events = TrackingEvent.query.all()
            assert len(events) == count_before + 1
            assert events[-1].user_id is not None

    def test_track_records_in_db(self, client, app):
        from app.models.tracking import TrackingEvent
        with app.app_context():
            count_before = TrackingEvent.query.count()
            client.post('/api/events/track', json=[
                {'event_type': 'favorite', 'event_data': {'hotel_id': 'h001', 'action': 'added'}}
            ])
            events = TrackingEvent.query.all()
            assert len(events) == count_before + 1
            assert events[-1].event_type == 'favorite'

    def test_track_empty_event_type_skipped(self, client):
        resp = client.post('/api/events/track', json=[
            {'event_type': '', 'page': '/test'},
            {'event_type': 'pageview', 'page': '/test'},
        ])
        assert resp.status_code == 200
        assert resp.get_json()['data']['count'] == 1
