"""Payment and subscription flow tests."""


class TestPaymentPlans:
    def test_get_plans(self, client):
        resp = client.get('/api/payment/plans')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        plans = data['data']['plans']
        assert len(plans) >= 2
        plan_ids = [p['id'] for p in plans]
        assert 'monthly' in plan_ids
        assert 'yearly' in plan_ids
        # Verify plan structure
        for plan in plans:
            assert 'name' in plan
            assert 'price' in plan
            assert 'days' in plan
            assert 'features' in plan


class TestPaymentCreate:
    def test_create_payment_monthly(self, client, auth_headers):
        resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly',
            'payment_provider': 'wechat',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['payment_provider'] == 'wechat'
        assert 'subscription_id' in data['data']

    def test_create_payment_yearly(self, client, auth_headers):
        resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'yearly',
            'payment_provider': 'alipay',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['payment_provider'] == 'alipay'

    def test_create_payment_invalid_plan(self, client, auth_headers):
        resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'weekly',
            'payment_provider': 'wechat',
        })
        assert resp.status_code == 400

    def test_create_payment_invalid_provider(self, client, auth_headers):
        resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly',
            'payment_provider': 'paypal',
        })
        assert resp.status_code == 400

    def test_create_payment_requires_auth(self, client):
        resp = client.post('/api/payment/create', json={
            'plan': 'monthly',
            'payment_provider': 'wechat',
        })
        assert resp.status_code in (401, 422)


class TestMockPayment:
    def test_mock_payment_flow(self, client, auth_headers):
        """Full flow: create order → mock pay → verify membership activated."""
        # 1. Create payment
        create_resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly',
            'payment_provider': 'wechat',
        })
        sub_id = create_resp.get_json()['data']['subscription_id']

        # 2. Mock pay
        mock_resp = client.get(f'/api/payment/mock/wechat/{sub_id}', headers=auth_headers)
        assert mock_resp.status_code == 200
        assert mock_resp.get_json()['success'] is True

        # 3. Verify membership upgraded
        info_resp = client.get('/api/membership/info', headers=auth_headers)
        data = info_resp.get_json()['data']
        assert data['tier'] == 'premium'
        assert data['is_member'] is True
        assert data['search_remaining'] == -1  # Unlimited

    def test_mock_payment_status(self, client, auth_headers):
        create_resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly',
            'payment_provider': 'alipay',
        })
        sub_id = create_resp.get_json()['data']['subscription_id']

        resp = client.get(f'/api/payment/status/{sub_id}', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['status'] == 'pending'

    def test_mock_payment_nonexistent(self, client, auth_headers):
        resp = client.get('/api/payment/mock/wechat/99999', headers=auth_headers)
        assert resp.status_code == 404

    def test_mock_payment_wrong_user(self, client, auth_headers, auth_headers_alt):
        create_resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly',
            'payment_provider': 'wechat',
        })
        sub_id = create_resp.get_json()['data']['subscription_id']

        # Try to mock pay with different user's token
        resp = client.get(f'/api/payment/mock/wechat/{sub_id}', headers=auth_headers_alt)
        assert resp.status_code == 403

    def test_membership_extends_on_renewal(self, client, auth_headers):
        """When renewing before expiry, days should be added to existing expiry."""
        # First payment
        create_resp = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly', 'payment_provider': 'wechat',
        })
        sub_id = create_resp.get_json()['data']['subscription_id']
        client.get(f'/api/payment/mock/wechat/{sub_id}', headers=auth_headers)

        # Get expiry after first payment
        info1 = client.get('/api/membership/info', headers=auth_headers).get_json()['data']
        expires_at_1 = info1['expires_at']

        # Second payment (renewal)
        create_resp2 = client.post('/api/payment/create', headers=auth_headers, json={
            'plan': 'monthly', 'payment_provider': 'alipay',
        })
        sub_id2 = create_resp2.get_json()['data']['subscription_id']
        client.get(f'/api/payment/mock/alipay/{sub_id2}', headers=auth_headers)

        info2 = client.get('/api/membership/info', headers=auth_headers).get_json()['data']
        expires_at_2 = info2['expires_at']

        # Expiry should be extended
        assert expires_at_2 > expires_at_1


class TestPaymentCallbacks:
    def test_wechat_callback_invalid(self, client):
        resp = client.post('/api/payment/wechat/callback', json={})
        assert resp.status_code == 400

    def test_alipay_callback_invalid(self, client):
        resp = client.post('/api/payment/alipay/callback', data={})
        assert resp.status_code == 400
