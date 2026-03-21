"""
Serper.dev Service for Hotel Price Comparison
Searches external booking platforms (Booking.com, KAYAK, TripAdvisor, etc.)
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class SerperService:
    """
    Serper.dev API client for searching hotel prices on external platforms.

    Serper returns Google search results, from which we extract:
    - Platform identification (Booking, KAYAK, TripAdvisor, etc.)
    - Price information (if available in snippet)
    - Direct links to booking pages
    """

    SERPER_API_URL = "https://google.serper.dev/search"
    DEFAULT_TIMEOUT = 15  # Increased from 10 to 15 seconds

    # Platform configuration with domain patterns
    PLATFORM_CONFIG = {
        'booking': {
            'domains': ['booking.com', 'www.booking.com'],
            'name': 'Booking.com',
            'icon': 'bi-building'
        },
        'kayak': {
            'domains': ['kayak.com', 'www.kayak.com', 'cn.kayak.com'],
            'name': 'KAYAK',
            'icon': 'bi-search'
        },
        'tripadvisor': {
            'domains': ['tripadvisor.com', 'www.tripadvisor.com', 'tripadvisor.cn'],
            'name': 'TripAdvisor',
            'icon': 'bi-star'
        },
        'ctrip': {
            'domains': ['ctrip.com', 'trip.com', 'www.ctrip.com', 'www.trip.com'],
            'name': '携程/Trip.com',
            'icon': 'bi-airplane'
        },
        'expedia': {
            'domains': ['expedia.com', 'www.expedia.com'],
            'name': 'Expedia',
            'icon': 'bi-globe'
        },
        'agoda': {
            'domains': ['agoda.com', 'www.agoda.com'],
            'name': 'Agoda',
            'icon': 'bi-house'
        },
        'hotels': {
            'domains': ['hotels.com', 'www.hotels.com'],
            'name': 'Hotels.com',
            'icon': 'bi-building'
        }
    }

    def __init__(self, api_key: Optional[str] = None, timeout: int = None):
        """
        Initialize Serper service.

        Args:
            api_key: Serper API key (optional, will use env var if not provided)
            timeout: Request timeout in seconds (default: 15)
        """
        self.api_key = api_key
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        logger.debug(f"[Serper] Initialized with timeout={self.timeout}s, has_key={bool(api_key)}")

    def search_hotel_prices(
        self,
        hotel_name: str,
        city: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2
    ) -> Dict:
        """
        Search for hotel prices on external platforms using Serper.

        Args:
            hotel_name: Hotel name to search
            city: City name
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adult_count: Number of adults

        Returns:
            Dict with search results:
            {
                'query': str,
                'results': [
                    {
                        'platform': str,
                        'platform_name': str,
                        'title': str,
                        'snippet': str,
                        'price': float or None,
                        'currency': str,
                        'url': str
                    }
                ],
                'total_found': int
            }
        """
        if not self.api_key:
            logger.warning("[Serper] API key not configured, skipping search")
            return {'query': '', 'results': [], 'total_found': 0, 'error': 'API key not configured'}

        # Build search query
        query = self._build_search_query(hotel_name, city, check_in, check_out)
        logger.info(f"[Serper] Searching for: hotel={hotel_name}, city={city}, dates={check_in} to {check_out}")
        logger.info(f"[Serper] Query: {query}")

        try:
            # Call Serper API
            response = self._call_serper_api(query)
            if not response:
                return {'query': query, 'results': [], 'total_found': 0}

            # Parse organic results
            results = []
            organic_results = response.get('organic', [])
            logger.info(f"[Serper] Processing {len(organic_results)} organic results")

            for item in organic_results:
                url = item.get('link', '')
                platform_key = self._identify_platform(url)

                if not platform_key:
                    continue  # Skip non-hotel-booking sites

                platform_config = self.PLATFORM_CONFIG[platform_key]
                snippet = item.get('snippet', '')
                title = item.get('title', '')

                # Extract price from snippet or title
                price, currency = self._extract_price(snippet + ' ' + title)

                result = {
                    'platform': platform_key,
                    'platform_name': platform_config['name'],
                    'icon': platform_config['icon'],
                    'title': title,
                    'snippet': snippet,
                    'price': price,
                    'currency': currency,
                    'url': url
                }
                results.append(result)
                logger.info(f"[Serper] Found result: platform={platform_config['name']}, "
                           f"price={price}{currency}, title={title[:50]}...")

            # Sort by platform priority and price availability
            results = self._sort_results(results)

            logger.info(f"[Serper] Found {len(results)} external platform results")

            return {
                'query': query,
                'results': results,
                'total_found': len(results)
            }

        except Exception as e:
            logger.error(f"[Serper] Search error: {e}")
            return {'query': query, 'results': [], 'total_found': 0}

    def _build_search_query(
        self,
        hotel_name: str,
        city: str,
        check_in: str,
        check_out: str
    ) -> str:
        """
        Build search query for hotel prices with date information.

        Includes date parameters to get more relevant pricing results.
        """
        parts = []

        # Hotel name (without quotes to avoid API restrictions)
        parts.append(hotel_name)

        # Add city information
        parts.append(city)

        # Add date information (key improvement for price relevance)
        if check_in:
            check_in_formatted = self._format_date(check_in)
            parts.append(f'{check_in_formatted}')
            if check_out:
                check_out_formatted = self._format_date(check_out)
                parts.append(f'{check_out_formatted}')

        # Add booking keyword
        parts.append('booking')

        query = ' '.join(parts)
        logger.debug(f"[Serper] Built query: {query}")
        return query

    def _format_date(self, date_str: str) -> str:
        """Format YYYY-MM-DD to more readable format."""
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%b %d')  # e.g., "Mar 20"
        except (ValueError, TypeError):
            return date_str

    def _call_serper_api(self, query: str) -> Optional[Dict]:
        """
        Call Serper API and return response.

        Args:
            query: Search query

        Returns:
            API response dict or None on error
        """
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'gl': 'cn',  # Geographic location
            'hl': 'zh-cn',  # Language
            'num': 30  # Number of results (increased for better coverage)
        }

        logger.info(f"[Serper] Calling API: URL={self.SERPER_API_URL}, query={query}")
        logger.debug(f"[Serper] Request payload: {payload}")

        try:
            response = requests.post(
                self.SERPER_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            logger.info(f"[Serper] API response: status={response.status_code}, "
                       f"content_length={len(response.text)} chars")

            if response.status_code == 200:
                data = response.json()
                organic_count = len(data.get('organic', []))
                logger.info(f"[Serper] Success: {organic_count} organic results returned")
                logger.debug(f"[Serper] Response keys: {list(data.keys())}")
                return data
            else:
                logger.error(f"[Serper] API error: {response.status_code} - {response.text[:500]}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"[Serper] API timeout after {self.timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[Serper] Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"[Serper] Unexpected error: {e}")
            return None

    def _extract_price(self, text: str) -> Tuple[Optional[float], str]:
        """
        Extract price from text using regex patterns.

        Patterns supported:
        - ¥1,234 or CNY 1,234
        - $123 or USD 123
        - €123 or EUR 123
        - 1,234元
        - 每晚 ¥1,234

        Returns:
            Tuple of (price, currency)
        """
        if not text:
            return None, 'CNY'

        # Price patterns with currency
        patterns = [
            # CNY patterns
            (r'[¥￥]\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'CNY\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'([\d,]+(?:\.\d{2})?)\s*元', 'CNY'),
            (r'人民币\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            # USD patterns
            (r'\$\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'USD\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            # EUR patterns
            (r'€\s*([\d,]+(?:\.\d{2})?)', 'EUR'),
            (r'EUR\s*([\d,]+(?:\.\d{2})?)', 'EUR'),
        ]

        for pattern, currency in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    # Filter out unreasonable prices (< 50 or > 50000)
                    if 50 <= price <= 50000:
                        return price, currency
                except ValueError:
                    continue

        return None, 'CNY'

    def _identify_platform(self, url: str) -> Optional[str]:
        """
        Identify booking platform from URL.

        Args:
            url: URL to analyze

        Returns:
            Platform key or None if not recognized
        """
        if not url:
            return None

        url_lower = url.lower()

        for platform_key, config in self.PLATFORM_CONFIG.items():
            for domain in config['domains']:
                if domain in url_lower:
                    return platform_key

        return None

    def _sort_results(self, results: List[Dict]) -> List[Dict]:
        """
        Sort results by priority.

        Priority:
        1. Results with prices first
        2. Platform priority (booking > kayak > ctrip > others)
        3. Results without prices
        """
        platform_priority = {
            'booking': 1,
            'kayak': 2,
            'ctrip': 3,
            'agoda': 4,
            'tripadvisor': 5,
            'expedia': 6,
            'hotels': 7
        }

        def sort_key(item):
            has_price = 0 if item.get('price') else 1
            priority = platform_priority.get(item.get('platform'), 99)
            return (has_price, priority)

        return sorted(results, key=sort_key)

    @staticmethod
    def normalize_for_comparison(serper_data: Dict) -> List[Dict]:
        """
        Normalize Serper results for comparison display.

        Args:
            serper_data: Raw Serper search results

        Returns:
            List of normalized comparison items
        """
        if not serper_data or not serper_data.get('results'):
            return []

        normalized = []
        seen_platforms = set()

        for item in serper_data['results']:
            platform = item.get('platform')

            # Only include one result per platform (the best one)
            if platform in seen_platforms:
                continue
            seen_platforms.add(platform)

            normalized.append({
                'platform': platform,
                'platform_name': item.get('platform_name', platform),
                'icon': item.get('icon', 'bi-link'),
                'price': item.get('price'),
                'currency': item.get('currency', 'CNY'),
                'url': item.get('url'),
                'title': item.get('title', ''),
                'is_external': True  # Flag to identify external platforms
            })

        return normalized
