"""
Hotel Matcher Service
Cross-platform hotel matching for price comparison
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class HotelMatcher:
    """Cross-platform hotel matching service."""

    # Name similarity threshold (0-1) - lowered for cross-platform matching
    NAME_SIMILARITY_THRESHOLD = 0.55

    # Maximum distance in meters for location match - increased for flexibility
    MAX_DISTANCE_METERS = 1000

    def __init__(self):
        pass

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two hotel names.

        Uses multiple strategies:
        1. Normalize names (remove common suffixes, lowercase)
        2. Calculate sequence similarity
        3. Check for brand match (including cross-language)

        Args:
            name1: First hotel name
            name2: Second hotel name

        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0

        # Normalize names
        norm1 = self._normalize_hotel_name(name1)
        norm2 = self._normalize_hotel_name(name2)

        # Exact match after normalization
        if norm1 == norm2:
            return 1.0

        # Sequence matcher
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # Check if one contains the other (partial match)
        if norm1 in norm2 or norm2 in norm1:
            similarity = max(similarity, 0.85)

        # Check brand match (including cross-language)
        brand1 = self._extract_brand(name1)
        brand2 = self._extract_brand(name2)
        if brand1 and brand2:
            if brand1 == brand2:
                # Same brand, boost similarity
                similarity = max(similarity, 0.7)
            elif self._are_same_brand(brand1, brand2):
                # Cross-language brand match (e.g., "希尔顿" vs "Hilton")
                similarity = max(similarity, 0.65)

        return similarity

    def _are_same_brand(self, brand1: str, brand2: str) -> bool:
        """
        Check if two brand names refer to the same brand (cross-language).

        Maps Chinese brand names to their English equivalents.
        """
        # Brand name mappings (Chinese -> English) - expanded list
        brand_mappings = {
            '希尔顿': 'Hilton',
            '万豪': 'Marriott',
            '喜来登': 'Sheraton',
            '洲际': 'InterContinental',
            '威斯汀': 'Westin',
            '凯悦': 'Hyatt',
            '四季': 'Four Seasons',
            '丽思卡尔顿': 'Ritz-Carlton',
            '香格里拉': 'Shangri-La',
            '半岛': 'Peninsula',
            '文华东方': 'Mandarin Oriental',
            '索菲特': 'Sofitel',
            '诺富特': 'Novotel',
            '皇冠假日': 'Crowne Plaza',
            '假日': 'Holiday Inn',
            '智选假日': 'Holiday Inn Express',
            '汉庭': 'Hanting',
            '如家': 'Home Inn',
            '锦江': 'Jin Jiang',
            '全季': 'JI Hotel',
            '亚朵': 'Atour',
            # Additional brands
            '华住': 'Huazhu',
            '桔子水晶': 'Crystal Orange',
            '桔子': 'Orange',
            '维也纳': 'Vienna',
            '7天': '7Days Inn',
            '7天连锁': '7Days Inn',
            '格林豪泰': 'GreenTree',
            '速8': 'Super 8',
            '布丁': 'Pod Inn',
            '宜必思': 'Ibis',
            '铂尔曼': 'Pullman',
            '瑞吉': 'St. Regis',
            '艾美': 'Le Meridien',
            '豪华精选': 'Luxury Collection',
            'W酒店': 'W Hotel',
            'W': 'W Hotel',
            '柏悦': 'Park Hyatt',
            '君悦': 'Grand Hyatt',
        }

        # Normalize both brands
        b1 = brand1.lower().strip()
        b2 = brand2.lower().strip()

        # Direct match
        if b1 == b2:
            return True

        # Check if either is a Chinese brand and maps to the other
        cn_to_en = {k.lower(): v.lower() for k, v in brand_mappings.items()}
        en_to_cn = {v.lower(): k.lower() for k, v in brand_mappings.items()}

        # Check Chinese -> English mapping
        if b1 in cn_to_en and cn_to_en[b1] == b2:
            return True
        if b2 in cn_to_en and cn_to_en[b2] == b1:
            return True

        # Check English -> Chinese mapping
        if b1 in en_to_cn and en_to_cn[b1] == b2:
            return True
        if b2 in en_to_cn and en_to_cn[b2] == b1:
            return True

        return False

    def _normalize_hotel_name(self, name: str) -> str:
        """
        Normalize hotel name for comparison.

        - Convert to lowercase
        - Remove common suffixes (Hotel, Inn, Resort, etc.)
        - Remove special characters
        - Normalize spaces
        """
        if not name:
            return ""

        # Convert to lowercase
        name = name.lower()

        # Remove common hotel suffixes (both English and Chinese)
        suffixes = [
            'hotel', 'inn', 'resort', 'suites', 'apartments',
            '酒店', '宾馆', '旅馆', '度假村', '公寓'
        ]
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Remove special characters, keep alphanumeric and Chinese
        name = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name)

        # Normalize spaces
        name = ' '.join(name.split())

        return name.strip()

    def _extract_brand(self, name: str) -> Optional[str]:
        """
        Extract brand name from hotel name.

        Common brands: Hilton, Marriott, Sheraton, etc.
        """
        if not name:
            return None

        # Common hotel brands
        brands = [
            'Hilton', 'Marriott', 'Sheraton', 'Hyatt', 'InterContinental',
            'Westin', 'Four Seasons', 'Ritz-Carlton', 'Shangri-La',
            'Mandarin Oriental', 'Peninsula', 'St. Regis', 'W Hotel',
            'Novotel', 'Accor', 'Ibis', 'Crowne Plaza', 'Holiday Inn',
            'Hampton', 'Courtyard', 'Fairfield', 'DoubleTree',
            '喜来登', '希尔顿', '万豪', '香格里拉', '洲际', '威斯汀',
            '凯悦', '四季', '丽思卡尔顿', '半岛', '文华东方'
        ]

        name_lower = name.lower()
        for brand in brands:
            if brand.lower() in name_lower:
                return brand

        return None

    def calculate_location_similarity(
        self,
        lat1: Optional[float],
        lng1: Optional[float],
        lat2: Optional[float],
        lng2: Optional[float]
    ) -> Tuple[bool, Optional[float]]:
        """
        Calculate location similarity based on coordinates.

        Args:
            lat1, lng1: First location coordinates
            lat2, lng2: Second location coordinates

        Returns:
            Tuple of (is_match, distance_in_meters)
        """
        if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
            return (False, None)

        try:
            # Calculate distance using Haversine formula
            distance = self._haversine_distance(lat1, lng1, lat2, lng2)
            is_match = distance <= self.MAX_DISTANCE_METERS
            return (is_match, distance)
        except Exception as e:
            logger.warning(f"Failed to calculate distance: {e}")
            return (False, None)

    def _haversine_distance(
        self,
        lat1: float,
        lng1: float,
        lat2: float,
        lng2: float
    ) -> float:
        """
        Calculate distance between two points in meters using Haversine formula.
        """
        import math

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lng1_rad = math.radians(lng1)
        lng2_rad = math.radians(lng2)

        # Earth radius in meters
        R = 6371000

        # Differences
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def match_hotels(
        self,
        source_hotel: Dict,
        candidate_hotels: List[Dict]
    ) -> List[Dict]:
        """
        Match source hotel against candidate hotels.

        Args:
            source_hotel: Source hotel with name, address, lat, lng
            candidate_hotels: List of candidate hotels to match against

        Returns:
            List of matched hotels with confidence score
        """
        matches = []

        source_name = source_hotel.get('name', '')
        source_lat = source_hotel.get('latitude')
        source_lng = source_hotel.get('longitude')
        source_address = source_hotel.get('address', '')

        logger.debug(f"[Matcher] Matching '{source_name}' against {len(candidate_hotels)} candidates")

        for candidate in candidate_hotels:
            candidate_name = candidate.get('name', '')
            candidate_lat = candidate.get('latitude')
            candidate_lng = candidate.get('longitude')

            # Calculate name similarity
            name_similarity = self.calculate_name_similarity(source_name, candidate_name)

            # Calculate location similarity
            location_match, distance = self.calculate_location_similarity(
                source_lat, source_lng, candidate_lat, candidate_lng
            )

            # Calculate overall confidence
            confidence = self._calculate_confidence(
                name_similarity,
                location_match,
                distance
            )

            # Only include if above threshold
            # Logic: match if confidence is high enough, OR name is very similar (0.8+), OR name+location both good
            if (confidence >= self.NAME_SIMILARITY_THRESHOLD or
                name_similarity >= 0.8 or  # Very high name similarity - likely same hotel
                (name_similarity >= 0.5 and location_match)):  # Reasonable name + location match
                logger.debug(f"[Matcher] Match accepted: '{candidate_name}' - "
                           f"conf={confidence:.2f}, name_sim={name_similarity:.2f}, "
                           f"loc_match={location_match}, dist={distance}m")
                matches.append({
                    **candidate,
                    'match_confidence': confidence,
                    'name_similarity': name_similarity,
                    'location_match': location_match,
                    'distance_meters': distance
                })
            else:
                # Log rejection for debugging (only for top candidates)
                if name_similarity >= 0.3:
                    logger.debug(f"[Matcher] Match rejected: '{candidate_name}' - "
                               f"conf={confidence:.2f}, name_sim={name_similarity:.2f}, "
                               f"loc_match={location_match}, dist={distance}m")

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x['match_confidence'], reverse=True)

        logger.debug(f"[Matcher] Found {len(matches)} matches for '{source_name}'")

        return matches

    def _calculate_confidence(
        self,
        name_similarity: float,
        location_match: bool,
        distance: Optional[float]
    ) -> float:
        """
        Calculate overall match confidence.

        Weights:
        - Name similarity: 60%
        - Location match: 40%
        """
        base_confidence = name_similarity * 0.6

        if location_match and distance is not None:
            # Higher confidence for closer locations
            location_score = max(0, 1 - (distance / (self.MAX_DISTANCE_METERS * 2)))
            base_confidence += location_score * 0.4

        return base_confidence

    def search_in_other_provider(
        self,
        hotel_info: Dict,
        target_provider: str,
        search_func
    ) -> List[Dict]:
        """
        Search for matching hotels in another provider.

        Args:
            hotel_info: Source hotel information
            target_provider: Target provider name
            search_func: Function to call for searching (provider.search_hotels)

        Returns:
            List of matched hotels with prices
        """
        try:
            # Build search query from hotel info
            query = hotel_info.get('name', '')
            place = hotel_info.get('address', '') or hotel_info.get('city', '')

            if not query:
                logger.warning("No hotel name for search")
                return []

            # Execute search
            logger.info(f"Searching {target_provider} for: {query}")

            # Different providers have different search params
            if target_provider == 'tuniu':
                # Tuniu requires city_name, check_in, check_out
                # Extract city from address
                city = self._extract_city(hotel_info.get('address', ''))
                result = search_func(
                    city_name=city,
                    check_in=hotel_info.get('check_in'),
                    check_out=hotel_info.get('check_out'),
                    keyword=query,
                    adult_count=hotel_info.get('adult_count', 2),
                    child_count=hotel_info.get('child_count', 0)
                )
            else:
                # RollingGo
                result = search_func(
                    query=query,
                    place=place,
                    place_type='酒店',
                    check_in_date=hotel_info.get('check_in'),
                    stay_nights=hotel_info.get('stay_nights', 1),
                    adult_count=hotel_info.get('adult_count', 2)
                )

            # Get hotels from result
            hotels = result.get('hotels', [])

            # Match hotels
            matched = self.match_hotels(hotel_info, hotels)

            logger.info(f"Found {len(matched)} matches in {target_provider}")

            return matched

        except Exception as e:
            logger.error(f"Error searching {target_provider}: {e}")
            return []

    def _extract_city(self, address: str) -> str:
        """
        Extract city name from address.

        Examples:
        - "北京市朝阳区建国路88号" -> "北京"
        - "上海市浦东新区" -> "上海"
        - "中国上海市浦东新区陆家嘴" -> "上海"
        """
        if not address:
            return ""

        # Expanded list of major cities (tier 1-3)
        major_cities = [
            # 一线城市
            '北京', '上海', '广州', '深圳',
            # 新一线城市
            '杭州', '成都', '南京', '武汉', '西安', '重庆', '天津', '苏州',
            '厦门', '青岛', '大连', '宁波', '无锡', '长沙', '郑州', '佛山',
            '东莞', '沈阳', '哈尔滨', '长春', '济南', '烟台', '福州', '合肥',
            # 热门旅游城市
            '三亚', '海口', '昆明', '丽江', '桂林', '张家界', '大理', '西双版纳',
            '珠海', '中山', '惠州', '汕头', '湛江',
            # 其他重要城市
            '常州', '南通', '嘉兴', '绍兴', '台州', '温州', '金华',
            '泉州', '南昌', '赣州', '九江', '太原', '大同', '石家庄', '唐山',
            '兰州', '乌鲁木齐', '银川', '西宁', '呼和浩特', '南宁', '桂林',
            '贵阳', '遵义', '海口', '三亚', '拉萨',
        ]

        # Province to city mapping for fallback
        province_city_map = {
            '北京': '北京', '上海': '上海', '天津': '天津', '重庆': '重庆',
            '广东': '广州', '浙江': '杭州', '江苏': '南京', '四川': '成都',
            '湖北': '武汉', '陕西': '西安', '山东': '济南', '福建': '福州',
            '湖南': '长沙', '河南': '郑州', '安徽': '合肥', '江西': '南昌',
            '河北': '石家庄', '山西': '太原', '辽宁': '沈阳', '吉林': '长春',
            '黑龙江': '哈尔滨', '云南': '昆明', '贵州': '贵阳', '广西': '南宁',
            '海南': '海口', '甘肃': '兰州', '青海': '西宁', '内蒙古': '呼和浩特',
            '新疆': '乌鲁木齐', '宁夏': '银川', '西藏': '拉萨',
        }

        # Try direct match for major cities first
        for city in major_cities:
            if city in address:
                logger.debug(f"City extracted from address: {city}")
                return city

        # Try to extract from "XX市" pattern
        match = re.search(r'([\u4e00-\u9fff]{2,4})市', address)
        if match:
            city = match.group(1)
            logger.debug(f"City extracted from '市' pattern: {city}")
            return city

        # Try to extract from province name
        for province, city in province_city_map.items():
            if province in address:
                logger.debug(f"City inferred from province {province}: {city}")
                return city

        # Try to match from "中国XX" pattern
        cn_match = re.search(r'中国[,，\s]*([\u4e00-\u9fff]{2,4})', address)
        if cn_match:
            potential_city = cn_match.group(1)
            # Check if it's a known city
            for city in major_cities:
                if city in potential_city or potential_city in city:
                    logger.debug(f"City extracted from '中国' pattern: {city}")
                    return city

        # Fallback: return first meaningful substring (2-4 Chinese chars)
        fallback_match = re.search(r'[\u4e00-\u9fff]{2,4}', address)
        if fallback_match:
            fallback = fallback_match.group(0)
            logger.debug(f"City fallback: {fallback}")
            return fallback

        logger.warning(f"Could not extract city from address: {address}")
        return ""
