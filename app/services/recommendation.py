"""
Recommendation service
Rule-based hotel recommendations using user behavior data
"""
import logging
from collections import Counter
from flask import current_app
from sqlalchemy import func
from app.models.database import db, SearchHistory, Favorite

logger = logging.getLogger(__name__)


class RecommendationService:
    """Rule-based hotel recommendation engine."""

    def get_personalized_suggestions(self, user_id, limit=10):
        """
        Get personalized hotel suggestions based on user behavior.

        Uses search history and favorites to extract preferences:
        - Frequently searched cities/places
        - Price range preferences
        - Star rating preferences
        """
        # Get user's search history
        searches = db.session.query(SearchHistory).filter_by(
            user_id=user_id
        ).order_by(SearchHistory.created_at.desc()).limit(50).all()

        # Get user's favorites
        favorites = db.session.query(Favorite).filter_by(
            user_id=user_id
        ).all()

        if not searches and not favorites:
            return []

        # Extract preferred places
        place_counter = Counter()
        for s in searches:
            if s.place:
                place_counter[s.place] += 1

        # Extract preferred providers
        provider_counter = Counter()
        for s in searches:
            if s.provider:
                provider_counter[s.provider] += 1

        # Top preferred place
        top_places = [p for p, _ in place_counter.most_common(3)]

        # Preferred provider
        top_provider = provider_counter.most_common(1)[0][0] if provider_counter else None

        # Build recommendations from recent searches
        recommendations = []
        seen = set()

        for place in top_places:
            # Find recent searches for this place
            place_searches = [s for s in searches if s.place == place][:3]
            for s in place_searches:
                rec = {
                    'place': s.place,
                    'place_type': s.place_type,
                    'provider': s.provider or top_provider,
                    'reason': 'based on your search history',
                }
                key = f"{rec['place']}:{rec['provider']}"
                if key not in seen:
                    seen.add(key)
                    recommendations.append(rec)

                if len(recommendations) >= limit:
                    break
            if len(recommendations) >= limit:
                break

        return recommendations[:limit]

    def get_similar_hotels(self, hotel_id, provider, limit=5):
        """
        Get similar hotel recommendations.
        Uses favorites and search history of other users who also favorited this hotel.
        """
        # Find users who favorited this hotel
        fav_users = db.session.query(Favorite.user_id).filter(
            Favorite.hotel_id == hotel_id,
            Favorite.user_id.isnot(None)
        ).distinct().limit(20).all()

        if not fav_users:
            return []

        user_ids = [f[0] for f in fav_users]

        # Find other hotels favorited by these users
        similar = db.session.query(
            Favorite.hotel_id,
            Favorite.hotel_name,
            Favorite.provider,
            func.count(Favorite.id).label('score')
        ).filter(
            Favorite.user_id.in_(user_ids),
            Favorite.hotel_id != hotel_id,
            Favorite.hotel_id.isnot(None)
        ).group_by(
            Favorite.hotel_id, Favorite.hotel_name, Favorite.provider
        ).order_by(
            func.count(Favorite.id).desc()
        ).limit(limit).all()

        return [{
            'hotel_id': s.hotel_id,
            'hotel_name': s.hotel_name,
            'provider': s.provider,
            'score': s.score,
        } for s in similar]


# Singleton
recommendation_service = RecommendationService()
