"""CPS click tracking tests."""


class TestClickTrack:
    def test_click_track_success(self, client):
        resp = client.get('/api/click/track?url=https://example.com/book&hotel_id=h001&provider=tuniu&hotel_name=TestHotel')
        assert resp.status_code == 302
        assert resp.headers['Location'] == 'https://example.com/book'

    def test_click_track_missing_url(self, client):
        resp = client.get('/api/click/track')
        assert resp.status_code == 400

    def test_click_track_invalid_url(self, client):
        resp = client.get('/api/click/track?url=not-a-url')
        assert resp.status_code == 400

    def test_click_track_records_in_db(self, client, app):
        from app.models.database import Click
        with app.app_context():
            # Count existing clicks before this request
            count_before = Click.query.count()
            client.get('/api/click/track?url=https://example.com/1&hotel_id=h002&provider=tuniu&hotel_name=Hotel2')
            clicks = Click.query.all()
            assert len(clicks) == count_before + 1
            assert clicks[-1].hotel_id == 'h002'
            assert clicks[-1].provider == 'tuniu'

    def test_click_track_with_auth(self, client, auth_headers, app):
        from app.models.database import Click
        with app.app_context():
            client.get('/api/click/track?url=https://example.com/2&hotel_id=h003&provider=tuniu&hotel_name=Hotel3',
                       headers=auth_headers)
            click = Click.query.filter_by(hotel_id='h003').first()
            assert click is not None
            assert click.user_id is not None
