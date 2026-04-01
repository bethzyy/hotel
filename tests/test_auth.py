"""Authentication flow tests."""


class TestSendCode:
    def test_send_code_success(self, client):
        resp = client.post('/api/auth/send-code', json={'phone': '13800138000'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'code' in data  # Debug mode returns code
        assert len(data['code']) == 6

    def test_send_code_invalid_phone(self, client):
        resp = client.post('/api/auth/send-code', json={'phone': '12345'})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_send_code_missing_phone(self, client):
        resp = client.post('/api/auth/send-code', json={})
        assert resp.status_code == 400

    def test_send_code_empty_body(self, client):
        resp = client.post('/api/auth/send-code')
        # Flask returns 415 when POST without JSON content type
        assert resp.status_code in (400, 415)


class TestLogin:
    def test_login_success(self, client):
        # First send code
        client.post('/api/auth/send-code', json={'phone': '13800138000'})
        # Login with any code (in debug mode, the code is returned)
        resp = client.post('/api/auth/login', json={'phone': '13800138000', 'code': '000000'})
        # First attempt might fail if code mismatch, but registration should work
        # In debug mode the actual code is returned, let's get it properly
        send_resp = client.post('/api/auth/send-code', json={'phone': '13800138001'})
        code = send_resp.get_json()['code']
        resp = client.post('/api/auth/login', json={'phone': '13800138001', 'code': code})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['phone'] == '13800138001'

    def test_login_wrong_code(self, client):
        client.post('/api/auth/send-code', json={'phone': '13800138002'})
        resp = client.post('/api/auth/login', json={'phone': '13800138002', 'code': '999999'})
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post('/api/auth/login', json={'phone': '13800138003'})
        assert resp.status_code == 400


class TestGetCurrentUser:
    def test_me_authenticated(self, client, auth_headers):
        resp = client.get('/api/auth/me', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['authenticated'] is True
        assert 'user' in data['data']
        assert 'membership' in data['data']

    def test_me_anonymous(self, client):
        resp = client.get('/api/auth/me')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['authenticated'] is False
        assert 'device_fingerprint' in data['data']

    def test_me_invalid_token(self, client):
        resp = client.get('/api/auth/me', headers={'Authorization': 'Bearer invalid_token'})
        # Flask-JWT-Extended returns 422 for invalid tokens with optional=True
        assert resp.status_code in (200, 422)
        data = resp.get_json()
        # Invalid token should fall back to anonymous (200) or return error (422)
        if resp.status_code == 200:
            assert data['data']['authenticated'] is False


class TestAnonymous:
    def test_anonymous_session(self, client):
        resp = client.post('/api/auth/anonymous')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['authenticated'] is False
        assert len(data['data']['device_fingerprint']) > 0
