"""
Shared utility functions for route handlers.
"""
import hashlib
import json
from flask import current_app


def get_cache_service():
    """Get cache service from app context."""
    return current_app.cache_service


def generate_cache_key(prefix: str, data: dict) -> str:
    """Generate cache key from data."""
    data_str = json.dumps(data, sort_keys=True)
    return f"{prefix}:{hashlib.sha256(data_str.encode()).hexdigest()}"
