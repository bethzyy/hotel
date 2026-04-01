"""
Shared test fixtures for hotel project tests.
Uses in-memory SQLite and Flask test client.
"""
import os
import tempfile

import pytest

# Force test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['FLASK_DEBUG'] = 'True'
os.environ['REDIS_URL'] = ''  # Use memory limiter, not Redis
os.environ['ADMIN_PASSWORD'] = 'testpassword'  # Admin API auth

from app import create_app
from app.models.database import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing with in-memory SQLite."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'DEBUG': True,
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False,  # Disable rate limiting in tests
    })

    # Create all tables
    with app.app_context():
        _db.create_all()

    yield app

    # Cleanup (ignore Windows file lock errors)
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except PermissionError:
        pass


@pytest.fixture(scope='function')
def db(app):
    """Fresh database session for each test."""
    with app.app_context():
        yield _db
        _db.session.remove()
        _db.drop_all()
        _db.create_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope='session')
def auth_headers(app):
    """Get JWT auth headers for a test user (phone: 13800138000). Session-scoped to avoid rate limiting."""
    client = app.test_client()
    # Send verification code
    resp = client.post('/api/auth/send-code', json={'phone': '13800138000'})
    code = resp.get_json()['code']

    # Login
    resp = client.post('/api/auth/login', json={'phone': '13800138000', 'code': code})
    token = resp.get_json()['data']['access_token']

    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='session')
def auth_headers_alt(app):
    """Get JWT auth headers for a second test user (phone: 13900139000). Session-scoped."""
    client = app.test_client()
    resp = client.post('/api/auth/send-code', json={'phone': '13900139000'})
    code = resp.get_json()['code']

    resp = client.post('/api/auth/login', json={'phone': '13900139000', 'code': code})
    token = resp.get_json()['data']['access_token']

    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers():
    """Basic auth headers for admin API."""
    from base64 import b64encode
    credentials = b64encode(b'admin:testpassword').decode()
    return {'Authorization': f'Basic {credentials}'}
