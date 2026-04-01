"""Coupon system tests."""
from app.models.database import db


class TestCouponAvailable:
    def test_list_available_empty(self, client):
        resp = client.get('/api/coupons/available')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['coupons'] == []


class TestCouponClaimAndRedeem:
    def test_full_coupon_flow(self, client, auth_headers, app):
        from app.models.coupon import Coupon
        with app.app_context():
            coupon = Coupon(
                code='TEST20',
                name='8折优惠券',
                discount_type='percentage',
                discount_value=20,
                is_active=True,
            )
            db.session.add(coupon)
            db.session.commit()
            coupon_id = coupon.id  # Save ID before exiting context

        # 1. List available
        resp = client.get('/api/coupons/available')
        coupons = resp.get_json()['data']['coupons']
        assert len(coupons) >= 1

        # 2. Claim
        resp = client.post(f'/api/coupons/{coupon_id}/claim', headers=auth_headers)
        assert resp.status_code == 200

        # 3. Check mine
        resp = client.get('/api/coupons/mine', headers=auth_headers)
        my_coupons = resp.get_json()['data']['coupons']
        assert len(my_coupons) >= 1
        assert my_coupons[0]['status'] == 'unused'

        # 4. Redeem
        user_coupon_id = my_coupons[0]['id']
        resp = client.post('/api/coupons/redeem', headers=auth_headers, json={
            'coupon_id': user_coupon_id
        })
        assert resp.status_code == 200

        # 5. Verify used
        resp = client.get('/api/coupons/mine?status=used', headers=auth_headers)
        used_coupons = resp.get_json()['data']['coupons']
        assert any(c['status'] == 'used' for c in used_coupons)

    def test_claim_nonexistent_coupon(self, client, auth_headers):
        resp = client.post('/api/coupons/99999/claim', headers=auth_headers)
        assert resp.status_code == 404

    def test_claim_twice(self, client, auth_headers, app):
        from app.models.coupon import Coupon
        with app.app_context():
            coupon = Coupon(
                code='TEST30',
                name='7天优惠券',
                discount_type='fixed_days',
                discount_value=7,
                is_active=True,
            )
            db.session.add(coupon)
            db.session.commit()
            coupon_id = coupon.id

        client.post(f'/api/coupons/{coupon_id}/claim', headers=auth_headers)
        resp = client.post(f'/api/coupons/{coupon_id}/claim', headers=auth_headers)
        assert resp.status_code == 400

    def test_redeem_used_coupon(self, client, auth_headers, app):
        from app.models.coupon import Coupon
        with app.app_context():
            coupon = Coupon(
                code='USED',
                name='已用优惠券',
                discount_type='percentage',
                discount_value=10,
                is_active=True,
            )
            db.session.add(coupon)
            db.session.commit()
            coupon_id = coupon.id

        client.post(f'/api/coupons/{coupon_id}/claim', headers=auth_headers)
        mine = client.get('/api/coupons/mine', headers=auth_headers).get_json()['data']['coupons']
        uc_id = mine[0]['id']
        client.post('/api/coupons/redeem', headers=auth_headers, json={'coupon_id': uc_id})

        resp = client.post('/api/coupons/redeem', headers=auth_headers, json={'coupon_id': uc_id})
        assert resp.status_code == 400

    def test_redeem_nonexistent(self, client, auth_headers):
        resp = client.post('/api/coupons/redeem', headers=auth_headers, json={'coupon_id': 99999})
        assert resp.status_code == 404
