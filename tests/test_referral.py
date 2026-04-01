"""Referral system tests."""


class TestReferralCode:
    def test_get_referral_code(self, client, auth_headers):
        resp = client.get('/api/referral/code', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['data']['code']) == 6
        assert data['data']['total_referrals'] == 0
        assert data['data']['reward_days'] == 7

    def test_referral_code_persistent(self, client, auth_headers):
        """Same user should get same code on second request."""
        code1 = client.get('/api/referral/code', headers=auth_headers).get_json()['data']['code']
        code2 = client.get('/api/referral/code', headers=auth_headers).get_json()['data']['code']
        assert code1 == code2

    def test_referral_code_requires_auth(self, client):
        resp = client.get('/api/referral/code')
        assert resp.status_code in (401, 422)


class TestReferralApply:
    def test_apply_referral_success(self, client, auth_headers, auth_headers_alt):
        # Get referrer's code
        code = client.get('/api/referral/code', headers=auth_headers).get_json()['data']['code']

        # Apply with referred user
        resp = client.post('/api/referral/apply', headers=auth_headers_alt, json={'code': code})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert '7' in data['message']

        # Verify both users got membership
        for headers in [auth_headers, auth_headers_alt]:
            info = client.get('/api/membership/info', headers=headers).get_json()['data']
            assert info['is_member'] is True

    def test_apply_invalid_code(self, client, auth_headers_alt):
        resp = client.post('/api/referral/apply', headers=auth_headers_alt, json={'code': 'INVALID'})
        assert resp.status_code == 404

    def test_apply_self_referral(self, client, auth_headers):
        code = client.get('/api/referral/code', headers=auth_headers).get_json()['data']['code']
        resp = client.post('/api/referral/apply', headers=auth_headers, json={'code': code})
        assert resp.status_code == 400

    def test_apply_duplicate(self, client, auth_headers, auth_headers_alt):
        code = client.get('/api/referral/code', headers=auth_headers).get_json()['data']['code']
        client.post('/api/referral/apply', headers=auth_headers_alt, json={'code': code})
        # Second attempt
        resp = client.post('/api/referral/apply', headers=auth_headers_alt, json={'code': code})
        assert resp.status_code == 400

    def test_apply_missing_code(self, client, auth_headers_alt):
        resp = client.post('/api/referral/apply', headers=auth_headers_alt, json={})
        assert resp.status_code == 400


class TestReferralRecords:
    def test_get_records(self, client, auth_headers, auth_headers_alt):
        code = client.get('/api/referral/code', headers=auth_headers).get_json()['data']['code']
        client.post('/api/referral/apply', headers=auth_headers_alt, json={'code': code})

        resp = client.get('/api/referral/records', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['data']['records']) == 1
