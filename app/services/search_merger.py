"""
Search Merger Service
Merges results from multiple hotel providers (Tuniu + RollingGo)
Uses hotel_matcher for cross-provider deduplication
"""
import logging
from typing import Any, Dict, List, Optional

from app.services.hotel_matcher import HotelMatcher

logger = logging.getLogger(__name__)


class SearchMerger:
    """Merges hotel search results from Tuniu and RollingGo."""

    def __init__(self) -> None:
        self._matcher = HotelMatcher()

    def merge(
        self,
        tuniu_hotels: List[Dict[str, Any]],
        rollinggo_hotels: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Merge Tuniu and RollingGo results into a single deduplicated list.

        Strategy:
        1. Tuniu results take priority (booking + room info).
        2. For each Tuniu hotel, find matching RollingGo hotel via HotelMatcher.
        3. Merge fields from RollingGo into Tuniu entry.
        4. Append unmatched RollingGo hotels to the end.
        5. Sort by price ascending.

        Args:
            tuniu_hotels: Normalized hotel list from Tuniu provider.
            rollinggo_hotels: Normalized hotel list from RollingGo provider.

        Returns:
            Dict with keys: hotels, total, sources
        """
        tuniu_count = len(tuniu_hotels)
        rg_count = len(rollinggo_hotels)
        logger.info(
            "[Merger] Merging %d Tuniu + %d RollingGo hotels",
            tuniu_count, rg_count,
        )

        if not tuniu_hotels and not rollinggo_hotels:
            return self._empty_result()

        # Fast path: only one provider has results
        if not tuniu_hotels:
            return self._single_provider_result(rollinggo_hotels, 'rollinggo')
        if not rollinggo_hotels:
            return self._single_provider_result(tuniu_hotels, 'tuniu')

        matched_rg_ids: set = set()
        merged: List[Dict[str, Any]] = []
        merged_count = 0

        # --- Phase 1: Walk Tuniu hotels, try to match RollingGo ---
        for tn_hotel in tuniu_hotels:
            matches = self._matcher.match_hotels(tn_hotel, rollinggo_hotels)

            if matches:
                best = matches[0]  # already sorted by confidence desc
                rg_hotel = {k: v for k, v in best.items()
                            if k not in ('match_confidence', 'name_similarity',
                                         'location_match', 'distance_meters')}
                matched_rg_ids.add(rg_hotel.get('hotel_id', ''))
                merged_hotel = self._merge_fields(tn_hotel, rg_hotel)
                merged_hotel['_match_confidence'] = round(best['match_confidence'], 2)
                merged.append(merged_hotel)
                merged_count += 1
                logger.debug(
                    "[Merger] Matched: '%s' ↔ '%s' (conf=%.2f)",
                    tn_hotel.get('name', '')[:20],
                    rg_hotel.get('name', '')[:20],
                    best['match_confidence'],
                )
            else:
                # Tuniu-only hotel
                merged.append(self._enrich_tuniu_only(tn_hotel))

        # --- Phase 2: Append unmatched RollingGo hotels ---
        unmatched_rg = [
            h for h in rollinggo_hotels
            if h.get('hotel_id', '') not in matched_rg_ids
        ]
        for rg_hotel in unmatched_rg:
            merged.append(self._enrich_rollinggo_only(rg_hotel))

        tuniu_only = len([h for h in merged if h.get('_sources') == ['tuniu']])
        logger.info(
            "[Merger] Result: %d hotels (%d merged, %d tuniu-only, %d rg-only)",
            len(merged), merged_count, tuniu_only, len(unmatched_rg),
        )

        # --- Phase 3: Sort by price ---
        merged.sort(key=lambda h: h.get('price_per_night') or float('inf'))

        return {
            'hotels': merged,
            'total': len(merged),
            'sources': {
                'tuniu': tuniu_count,
                'rollinggo': rg_count,
                'merged_pairs': merged_count,
            },
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_fields(
        tn: Dict[str, Any],
        rg: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Field-level merge of a matched Tuniu + RollingGo hotel.

        Rules (per spec):
        - hotel_id: keep Tuniu (needed for booking), store rg id separately
        - name: Tuniu first
        - price_per_night: Tuniu first (real-time), fallback to RollingGo
        - distance / latitude / longitude: RollingGo first
        - amenities / tags / description: RollingGo only
        - booking_url: RollingGo only
        - business / brand_name / room_name / meal / refund / comment_digest: Tuniu only
        - currency: infer from providers
        """
        merged: Dict[str, Any] = {}

        # --- IDs ---
        merged['hotel_id'] = tn.get('hotel_id')
        merged['rollinggo_hotel_id'] = rg.get('hotel_id')

        # --- Name: Tuniu first ---
        merged['name'] = tn.get('name') or rg.get('name', '')

        # --- Price: Tuniu first (real-time), fallback RollingGo ---
        merged['price_per_night'] = tn.get('price_per_night') or rg.get('price_per_night')

        # --- Star rating: Tuniu first ---
        merged['star_rating'] = tn.get('star_rating') or rg.get('star_rating')
        merged['star_name'] = tn.get('star_name')

        # --- Image: prefer Tuniu, fallback RollingGo ---
        merged['image_url'] = tn.get('image_url') or rg.get('image_url')

        # --- Address: Tuniu first (more detailed for domestic) ---
        merged['address'] = tn.get('address') or rg.get('address')

        # --- Location: RollingGo first (has lat/lng) ---
        merged['latitude'] = rg.get('latitude') or tn.get('latitude')
        merged['longitude'] = rg.get('longitude') or tn.get('longitude')
        merged['distance'] = rg.get('distance')

        # --- Tuniu-only fields ---
        for key in ('business', 'brand_name', 'room_name', 'meal', 'refund', 'comment_digest'):
            if tn.get(key) is not None:
                merged[key] = tn[key]

        # --- RollingGo-only fields ---
        for key in ('amenities', 'description', 'tags', 'booking_url', 'country'):
            if rg.get(key) is not None:
                merged[key] = rg[key]

        # --- Currency ---
        merged['currency'] = tn.get('currency', 'CNY')

        # --- Source tracking ---
        merged['_sources'] = ['tuniu', 'rollinggo']

        return merged

    @staticmethod
    def _enrich_tuniu_only(hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Tag a Tuniu-only hotel with source metadata."""
        out = dict(hotel)
        out.setdefault('currency', 'CNY')
        out['_sources'] = ['tuniu']
        return out

    @staticmethod
    def _enrich_rollinggo_only(hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Tag a RollingGo-only hotel with source metadata."""
        out = dict(hotel)
        out.setdefault('currency', 'CNY')
        out['_sources'] = ['rollinggo']
        return out

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {
            'hotels': [],
            'total': 0,
            'sources': {'tuniu': 0, 'rollinggo': 0, 'merged_pairs': 0},
        }

    @staticmethod
    def _single_provider_result(
        hotels: List[Dict[str, Any]],
        provider: str,
    ) -> Dict[str, Any]:
        """Wrap a single-provider result in the standard format."""
        for h in hotels:
            h.setdefault('currency', 'CNY')
            h['_sources'] = [provider]
        hotels.sort(key=lambda h: h.get('price_per_night') or float('inf'))
        return {
            'hotels': hotels,
            'total': len(hotels),
            'sources': {provider: len(hotels), 'merged_pairs': 0},
        }
