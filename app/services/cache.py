"""
Cache service with Redis backend (production) or SQLite fallback (development).
"""
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict


class CacheService:
    """Service for caching API responses. Uses Redis when available, SQLite otherwise."""

    def __init__(self, db_path: str, redis_url: str = ''):
        self.db_path = db_path
        self._conn = None
        self._redis = None

        if redis_url:
            try:
                import redis
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    @property
    def conn(self):
        """Get SQLite connection (fallback). Only used when Redis is not available."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self):
        """Initialize SQLite fallback tables (only when Redis is not available)."""
        if self._redis is not None:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            self.conn.commit()
        except Exception:
            pass

    # ==================== Cache Methods ====================

    def get_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if not expired."""
        if self._redis:
            try:
                data = self._redis.get(f'api_cache:{cache_key}')
                if data:
                    return json.loads(data)
            except Exception:
                pass
            return None

        # SQLite fallback
        cursor = self.conn.cursor()
        cursor.execute('SELECT response, expires_at FROM api_cache WHERE cache_key = ?', (cache_key,))
        row = cursor.fetchone()
        if row is None:
            return None
        if row['expires_at']:
            from datetime import timezone
            expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                self.delete_cache(cache_key)
                return None
        try:
            return json.loads(row['response'])
        except json.JSONDecodeError:
            return None

    def set_cache(self, cache_key: str, response: Dict, ttl_seconds: int = 3600):
        """Store response in cache with TTL."""
        if self._redis:
            try:
                self._redis.setex(
                    f'api_cache:{cache_key}',
                    ttl_seconds,
                    json.dumps(response, ensure_ascii=False)
                )
                return
            except Exception:
                pass

        # SQLite fallback
        try:
            from datetime import timezone as tz
            now_utc = datetime.now(tz.utc)
            expires_ts = now_utc.timestamp() + ttl_seconds
            expires_dt = datetime.fromtimestamp(expires_ts, tz=tz.utc)
            expires_at_str = expires_dt.isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO api_cache (cache_key, response, expires_at) VALUES (?, ?, ?)',
                (cache_key, json.dumps(response), expires_at_str)
            )
            self.conn.commit()
        except Exception:
            pass

    def delete_cache(self, cache_key: str):
        """Delete cached response."""
        if self._redis:
            try:
                self._redis.delete(f'api_cache:{cache_key}')
            except Exception:
                pass
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM api_cache WHERE cache_key = ?', (cache_key,))
            self.conn.commit()
        except Exception:
            pass

    def clear_expired_cache(self):
        """Remove expired cache entries. No-op for Redis (TTL is automatic)."""
        if self._redis:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM api_cache WHERE expires_at IS NOT NULL AND expires_at < ?',
                            (datetime.now().isoformat(),))
            self.conn.commit()
        except Exception:
            pass

    # ==================== Compatibility Methods (delegate to SQLAlchemy) ====================

    def is_favorite(self, hotel_id: str) -> bool:
        """Check if hotel is in favorites (any user or anonymous)."""
        try:
            from app.models.database import Favorite
            return Favorite.query.filter_by(hotel_id=hotel_id).first() is not None
        except Exception:
            return False

    def add_search_history(self, query: str, place: str, place_type=None, provider=None):
        """Add search to history (anonymous, no user context)."""
        try:
            from app.models.database import SearchHistory
            import hashlib
            ua, ip = '', ''
            try:
                from flask import request
                ua = request.headers.get('User-Agent', '')
                ip = request.remote_addr or ''
            except Exception:
                pass
            fp = hashlib.sha256(f"{ua}{ip}".encode()).hexdigest()[:32]
            history = SearchHistory(device_fingerprint=fp, query=query, place=place,
                                   place_type=place_type, provider=provider)
            from app.models.database import db
            db.session.add(history)
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    def close(self):
        """Close database connections."""
        if self._conn:
            self._conn.close()
            self._conn = None
        if self._redis:
            try:
                self._redis.close()
            except Exception:
                pass
