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
        """Initialize database tables."""
        cursor = self.conn.cursor()

        # API response cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')

        # Favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_id TEXT UNIQUE NOT NULL,
                hotel_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                place TEXT NOT NULL,
                place_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.now() > expires_at:
                # Cache expired, delete and return None
                self.delete_cache(cache_key)
                return None

        try:
            return json.loads(row['response'])
        except json.JSONDecodeError:
            return None

    def set_cache(self, cache_key: str, response: Dict, ttl_seconds: int = 3600):
        """Store response in cache with TTL."""
        expires_at = datetime.now().timestamp() + ttl_seconds
        expires_at_str = datetime.fromtimestamp(expires_at).isoformat()

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

    # ==================== Favorites Methods ====================

    def add_favorite(self, hotel_id: str, hotel_data: Dict) -> bool:
        """Add hotel to favorites."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO favorites (hotel_id, hotel_data)
                VALUES (?, ?)
            ''', (hotel_id, json.dumps(hotel_data, ensure_ascii=False)))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def remove_favorite(self, hotel_id: str) -> bool:
        """Remove hotel from favorites."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM favorites WHERE hotel_id = ?', (hotel_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def is_favorite(self, hotel_id: str) -> bool:
        """Check if hotel is in favorites."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM favorites WHERE hotel_id = ?', (hotel_id,))
        return cursor.fetchone() is not None

    def get_favorites(self) -> List[Dict]:
        """Get all favorite hotels."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT hotel_id, hotel_data, created_at
            FROM favorites
            ORDER BY created_at DESC
        ''')

        favorites = []
        for row in cursor.fetchall():
            try:
                hotel_data = json.loads(row['hotel_data'])
                hotel_data['is_favorite'] = True
                hotel_data['favorited_at'] = row['created_at']
                favorites.append(hotel_data)
            except json.JSONDecodeError:
                continue

        return favorites

    def get_favorites_count(self) -> int:
        """Get total number of favorites."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM favorites')
        row = cursor.fetchone()
        return row['count'] if row else 0

    # ==================== Search History Methods ====================

    def add_search_history(self, query: str, place: str, place_type: Optional[str] = None):
        """Add search to history."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO search_history (query, place, place_type)
            VALUES (?, ?, ?)
        ''', (query, place, place_type))
        self.conn.commit()

    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """Get recent search history."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, query, place, place_type, created_at
            FROM search_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row['id'],
                'query': row['query'],
                'place': row['place'],
                'place_type': row['place_type'],
                'created_at': row['created_at']
            })

        return history

    def clear_search_history(self):
        """Clear all search history."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM search_history')
        self.conn.commit()

    def delete_search_history(self, history_id: int) -> bool:
        """Delete specific search history entry."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM search_history WHERE id = ?', (history_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    # ==================== Utility Methods ====================

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
