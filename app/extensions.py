"""
Shared Flask extension instances.
Import these in route modules to use decorators that must be applied at registration time.
"""
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Use Redis for rate limiting if available, fallback to memory
_redis_url = os.environ.get('REDIS_URL', '')
_storage_uri = _redis_url if _redis_url else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=_storage_uri,
    headers_enabled=True
)
