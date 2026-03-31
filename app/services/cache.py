"""
Cache and local storage service using SQLite
"""
import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class CacheService:
    """Service for caching API responses and storing user data."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    @property
    def conn(self):
        """Get database connection with row factory."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init_db(self):
        """Initialize database tables. Only manages api_cache table now.
        Favorites, SearchHistory, and Clicks are managed by SQLAlchemy models."""
        cursor = self.conn.cursor()

        # API response cache table (only table managed by CacheService)
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

    # ==================== Cache Methods ====================

    def get_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if not expired."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT response, expires_at FROM api_cache
            WHERE cache_key = ?
        ''', (cache_key,))

        row = cursor.fetchone()
        if row is None:
            return None

        # Check expiration
        if row['expires_at']:
            from datetime import timezone
            expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            if now_utc > expires_at:
                # Cache expired, delete and return None
                self.delete_cache(cache_key)
                return None

        try:
            return json.loads(row['response'])
        except json.JSONDecodeError:
            return None

    def set_cache(self, cache_key: str, response: Dict, ttl_seconds: int = 3600):
        """Store response in cache with TTL."""
        from datetime import timezone as tz
        # Use UTC to match SQLite's CURRENT_TIMESTAMP
        now_utc = datetime.now(tz.utc)
        expires_ts = now_utc.timestamp() + ttl_seconds
        expires_dt = datetime.fromtimestamp(expires_ts, tz=tz.utc)
        expires_at_str = expires_dt.isoformat()

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO api_cache (cache_key, response, expires_at)
            VALUES (?, ?, ?)
        ''', (cache_key, json.dumps(response), expires_at_str))
        self.conn.commit()

    def delete_cache(self, cache_key: str):
        """Delete cached response."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM api_cache WHERE cache_key = ?', (cache_key,))
        self.conn.commit()

    def clear_expired_cache(self):
        """Remove all expired cache entries."""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM api_cache
            WHERE expires_at IS NOT NULL
            AND expires_at < ?
        ''', (datetime.now().isoformat(),))
        self.conn.commit()

    # ==================== Compatibility Methods (delegate to SQLAlchemy) ====================
    # These methods are kept for backward compatibility with search.py and hotel.py.
    # They query the new SQLAlchemy-managed favorites/search_history tables.

    def is_favorite(self, hotel_id: str) -> bool:
        """Check if hotel is in favorites (any user or anonymous)."""
        try:
            from app.models.database import Favorite
            return Favorite.query.filter_by(hotel_id=hotel_id).first() is not None
        except Exception:
            return False

    def add_search_history(self, query: str, place: str, place_type: Optional[str] = None,
                          provider: Optional[str] = None):
        """Add search to history (anonymous, no user context)."""
        try:
            from app.models.database import SearchHistory
            import hashlib
            ua = ''
            ip = ''
            # Lazy import flask request context
            try:
                from flask import request
                ua = request.headers.get('User-Agent', '')
                ip = request.remote_addr or ''
            except Exception:
                pass
            fp = hashlib.sha256(f"{ua}{ip}".encode()).hexdigest()[:32]
            history = SearchHistory(
                device_fingerprint=fp,
                query=query, place=place,
                place_type=place_type, provider=provider
            )
            from app.models.database import db
            db.session.add(history)
            db.session.commit()
        except Exception:
            pass

    # ==================== Utility Methods ====================

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
