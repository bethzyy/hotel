"""
Tavily Service for Hotel Price Search
Uses Tavily Search API to find hotel prices on external booking platforms
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class TavilyService:
    """
    Tavily Search API client for searching hotel prices on external platforms.

    Tavily is optimized for AI applications and provides clean, structured search results.
    """

    TAVILY_API_URL = "https://api.tavily.com/search"
    TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
    DEFAULT_TIMEOUT = 15
    DEFAULT_EXTRACT_TIMEOUT = 30

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
        },
        'priceline': {
            'domains': ['priceline.com', 'www.priceline.com'],
            'name': 'Priceline',
            'icon': 'bi-tag'
        },
        'hotwire': {
            'domains': ['hotwire.com', 'www.hotwire.com'],
            'name': 'Hotwire',
            'icon': 'bi-fire'
        }
    }

    def __init__(self, api_key: Optional[str] = None, timeout: int = None):
        """
        Initialize Tavily service.

        Args:
            api_key: Tavily API key (optional, will use env var if not provided)
            timeout: Request timeout in seconds (default: 15)
        """
        self.api_key = api_key
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        logger.debug(f"[Tavily] Initialized with timeout={self.timeout}s, has_key={bool(api_key)}")

    def search_hotel_prices(
        self,
        hotel_name: str,
        city: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2
    ) -> Dict:
        """
        Search for hotel prices on external platforms using Tavily.

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
                        'content': str,
                        'price': float or None,
                        'currency': str,
                        'url': str
                    }
                ],
                'total_found': int
            }
        """
        if not self.api_key:
            logger.warning("[Tavily] API key not configured, skipping search")
            return {'query': '', 'results': [], 'total_found': 0, 'error': 'API key not configured'}

        # Build search query
        query = self._build_search_query(hotel_name, city, check_in, check_out)
        logger.info(f"[Tavily] Searching for: hotel={hotel_name}, city={city}, dates={check_in} to {check_out}")
        logger.info(f"[Tavily] Query: {query}")

        try:
            # Call Tavily API
            response = self._call_tavily_api(query)
            if not response:
                logger.warning("[Tavily] API call returned no response")
                return {'query': query, 'results': [], 'total_found': 0}

            # Parse results
            results = []
            tavily_results = response.get('results', [])
            logger.info(f"[Tavily] Processing {len(tavily_results)} results from API")

            # Log raw response structure
            logger.debug(f"[Tavily] Response keys: {list(response.keys())}")
            if response.get('answer'):
                logger.debug(f"[Tavily] Answer: {response.get('answer')[:200]}...")

            skipped_urls = []
            for idx, item in enumerate(tavily_results):
                url = item.get('url', '')
                platform_key = self._identify_platform(url)

                if not platform_key:
                    # Log skipped URLs (non-hotel-booking sites)
                    domain = url.split('/')[2] if '/' in url[8:] else url[:50]
                    skipped_urls.append(domain)
                    logger.debug(f"[Tavily] Skipping result #{idx+1}: {domain} (not a booking platform)")
                    continue  # Skip non-hotel-booking sites

                platform_config = self.PLATFORM_CONFIG[platform_key]
                content = item.get('content', '')
                title = item.get('title', '')

                logger.info(f"[Tavily] Processing result #{idx+1}: platform={platform_config['name']}, url={url[:60]}...")
                logger.debug(f"[Tavily] Result #{idx+1} title: {title}")
                logger.debug(f"[Tavily] Result #{idx+1} content ({len(content)} chars): {content[:150]}...")

                # Extract price from content or title
                combined_text = content + ' ' + title
                price, currency = self._extract_price(combined_text)

                result = {
                    'platform': platform_key,
                    'platform_name': platform_config['name'],
                    'icon': platform_config['icon'],
                    'title': title,
                    'content': content,
                    'price': price,
                    'currency': currency,
                    'url': url
                }
                results.append(result)

                if price:
                    logger.info(f"[Tavily] ✓ Result #{idx+1}: {platform_config['name']} = {price}{currency}")
                else:
                    logger.info(f"[Tavily] ✗ Result #{idx+1}: {platform_config['name']} = No price found")

            if skipped_urls:
                logger.debug(f"[Tavily] Skipped {len(skipped_urls)} non-booking URLs: {skipped_urls[:5]}...")

            # Sort by platform priority and price availability
            results = self._sort_results(results)

            # Extract prices from URLs that don't have prices
            urls_without_price = [
                r['url'] for r in results
                if not r.get('price') and r.get('url')
            ]

            if urls_without_price:
                logger.info(f"[Tavily] Extracting prices from {len(urls_without_price)} URLs without price")
                extracted_prices = self.extract_prices_from_urls(urls_without_price)

                # Update results with extracted prices
                for result in results:
                    if not result.get('price') and result.get('url') in extracted_prices:
                        extracted = extracted_prices[result['url']]
                        if extracted.get('price'):
                            result['price'] = extracted['price']
                            result['currency'] = extracted['currency']
                            logger.info(f"[Tavily] Updated price for {result['platform']}: {result['price']} {result['currency']}")

                # Re-sort after getting new prices
                results = self._sort_results(results)

            logger.info(f"[Tavily] Found {len(results)} external platform results")

            return {
                'query': query,
                'results': results,
                'total_found': len(results)
            }

        except Exception as e:
            logger.error(f"[Tavily] Search error: {e}")
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
        """
        parts = []

        # Hotel name
        parts.append(hotel_name)

        # Add city information
        parts.append(city)

        # Add date information
        if check_in:
            check_in_formatted = self._format_date(check_in)
            parts.append(f'{check_in_formatted}')
            if check_out:
                check_out_formatted = self._format_date(check_out)
                parts.append(f'{check_out_formatted}')

        # Add booking keyword
        parts.append('booking price')

        query = ' '.join(parts)
        logger.debug(f"[Tavily] Built query: {query}")
        return query

    def _format_date(self, date_str: str) -> str:
        """Format YYYY-MM-DD to more readable format."""
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%b %d')  # e.g., "Mar 20"
        except (ValueError, TypeError):
            return date_str

    def _call_tavily_api(self, query: str) -> Optional[Dict]:
        """
        Call Tavily Search API and return response.

        Args:
            query: Search query

        Returns:
            API response dict or None on error
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Tavily API payload
        payload = {
            'query': query,
            'search_depth': 'basic',  # 'basic' or 'advanced'
            'include_domains': [],  # Empty means search all domains
            'exclude_domains': [],
            'include_raw_content': False,
            'max_results': 15,  # Number of results
            'include_answer': False,  # Don't need AI-generated answer
        }

        logger.info(f"[Tavily API] Calling: URL={self.TAVILY_API_URL}")
        logger.info(f"[Tavily API] Query: {query}")
        logger.debug(f"[Tavily API] Payload: search_depth={payload['search_depth']}, "
                    f"max_results={payload['max_results']}")

        try:
            import time
            start_time = time.time()

            response = requests.post(
                self.TAVILY_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"[Tavily API] Response: status={response.status_code}, "
                       f"time={elapsed_ms:.0f}ms, content_length={len(response.text)} chars")

            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                logger.info(f"[Tavily API] ✓ Success: {results_count} results returned")
                logger.debug(f"[Tavily API] Response keys: {list(data.keys())}")

                # Log first 3 results summary
                for i, r in enumerate(data.get('results', [])[:3]):
                    url = r.get('url', '')
                    title = r.get('title', '')[:50]
                    content_len = len(r.get('content', ''))
                    logger.debug(f"[Tavily API] Result #{i+1}: url={url[:60]}..., "
                               f"title={title}..., content={content_len} chars")

                return data
            else:
                logger.error(f"[Tavily API] ✗ API error: {response.status_code}")
                logger.error(f"[Tavily API] Response body: {response.text[:500]}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"[Tavily API] ✗ Timeout after {self.timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[Tavily API] ✗ Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"[Tavily API] ✗ Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def extract_prices_from_urls(self, urls: List[str]) -> Dict[str, Dict]:
        """
        Use Tavily Extract API to extract prices from web pages.

        Args:
            urls: List of URLs to extract prices from

        Returns:
            Dict mapping URL to {price, currency}
        """
        if not self.api_key or not urls:
            logger.debug(f"[Tavily Extract] Skipping extract: api_key={bool(self.api_key)}, urls_count={len(urls)}")
            return {}

        # Limit to 10 URLs per call (Tavily Extract API limit)
        urls_to_extract = urls[:10]

        try:
            logger.info(f"[Tavily Extract] Starting extraction for {len(urls_to_extract)} URLs")
            for i, url in enumerate(urls_to_extract):
                logger.debug(f"[Tavily Extract] URL #{i+1}: {url}")

            response = requests.post(
                self.TAVILY_EXTRACT_URL,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'urls': urls_to_extract,
                    'extract_depth': 'basic',
                    'include_images': False
                },
                timeout=self.DEFAULT_EXTRACT_TIMEOUT
            )

            logger.info(f"[Tavily Extract] API response: status={response.status_code}, "
                       f"content_length={len(response.text)} chars")

            if response.status_code == 200:
                data = response.json()
                results = {}
                extracted_count = 0

                logger.debug(f"[Tavily Extract] Response keys: {list(data.keys())}")
                api_results = data.get('results', [])
                logger.info(f"[Tavily Extract] Got {len(api_results)} extracted results")

                for idx, item in enumerate(api_results):
                    url = item.get('url', '')
                    raw_content = item.get('raw_content', '')

                    logger.debug(f"[Tavily Extract] Result #{idx+1}: url={url[:60]}..., "
                               f"content_length={len(raw_content) if raw_content else 0}")

                    if raw_content:
                        # Log sample of raw content
                        content_preview = raw_content[:300].replace('\n', ' ')
                        logger.debug(f"[Tavily Extract] Content preview: {content_preview}...")

                        # Extract price from the full page content
                        price, currency = self._extract_price(raw_content)
                        results[url] = {'price': price, 'currency': currency}

                        if price:
                            extracted_count += 1
                            logger.info(f"[Tavily Extract] ✓ Extracted: {price} {currency} from {url[:50]}...")
                        else:
                            logger.debug(f"[Tavily Extract] ✗ No price found in content for {url[:50]}...")
                    else:
                        logger.warning(f"[Tavily Extract] Result #{idx+1} has no raw_content")
                        results[url] = {'price': None, 'currency': 'CNY'}

                failed_count = len(data.get('failed', []))
                if failed_count > 0:
                    logger.warning(f"[Tavily Extract] {failed_count} URLs failed to extract: {data.get('failed', [])}")

                logger.info(f"[Tavily Extract] Summary: {extracted_count}/{len(urls_to_extract)} URLs had prices")
                return results
            else:
                logger.error(f"[Tavily Extract] API error: {response.status_code} - {response.text[:200]}")
                return {}

        except requests.exceptions.Timeout:
            logger.error(f"[Tavily Extract] API timeout after {self.DEFAULT_EXTRACT_TIMEOUT}s")
            return {}
        except Exception as e:
            logger.error(f"[Tavily Extract] Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    def _extract_price(self, text: str) -> Tuple[Optional[float], str]:
        """
        Extract price from text using regex patterns.

        Patterns supported:
        - ¥1,234 or CNY 1,234 (Chinese Yuan)
        - $123 or USD 123 (US Dollar)
        - €123 or EUR 123 (Euro)
        - £123 or GBP 123 (British Pound)
        - HK$1,234 or HKD 1,234 (Hong Kong Dollar)
        - NT$1,234 or TWD 1,234 (Taiwan Dollar)
        - 1,234元
        - 每晚 ¥1,234
        - per night $123
        - 价格/房价: ¥1,234
        - Range prices: $272 - $362 (takes the lower price)

        Returns:
            Tuple of (price, currency)
        """
        if not text:
            logger.debug("[Tavily Extract] Empty text, returning None")
            return None, 'CNY'

        # Log the text being analyzed (truncate for readability)
        text_preview = text[:200] + '...' if len(text) > 200 else text
        logger.debug(f"[Tavily Extract] Analyzing text ({len(text)} chars): {text_preview}")

        # Price patterns with currency (order matters - more specific first)
        patterns = [
            # === Range price patterns (extract lower price) ===
            (r'HK\$\s*([\d,]+(?:\.\d{2})?)\s*-\s*HK\$\s*[\d,]+(?:\.\d{2})?', 'HKD'),
            (r'NT\$\s*([\d,]+(?:\.\d{2})?)\s*-\s*NT\$\s*[\d,]+(?:\.\d{2})?', 'TWD'),
            (r'CN¥\s*([\d,]+(?:\.\d{2})?)\s*-\s*CN¥\s*[\d,]+(?:\.\d{2})?', 'CNY'),
            (r'¥\s*([\d,]+(?:\.\d{2})?)\s*-\s*¥\s*[\d,]+(?:\.\d{2})?', 'CNY'),
            (r'\$\s*([\d,]+(?:\.\d{2})?)\s*-\s*\$\s*[\d,]+(?:\.\d{2})?', 'USD'),
            (r'€\s*([\d,]+(?:\.\d{2})?)\s*-\s*€\s*[\d,]+(?:\.\d{2})?', 'EUR'),
            (r'£\s*([\d,]+(?:\.\d{2})?)\s*-\s*£\s*[\d,]+(?:\.\d{2})?', 'GBP'),

            # === HKD (Hong Kong Dollar) patterns ===
            (r'HK\$\s*([\d,]+(?:\.\d{2})?)', 'HKD'),
            (r'HKD\s*([\d,]+(?:\.\d{2})?)', 'HKD'),

            # === TWD (Taiwan Dollar) patterns ===
            (r'NT\$\s*([\d,]+(?:\.\d{2})?)', 'TWD'),
            (r'TWD\s*([\d,]+(?:\.\d{2})?)', 'TWD'),
            (r'新台幣\s*([\d,]+(?:\.\d{2})?)', 'TWD'),

            # === CNY (Chinese Yuan) patterns - specific hotel pricing formats ===
            (r'每晚\s*[¥￥]?\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'[¥￥]\s*([\d,]+(?:\.\d{2})?)\s*(?:/晚|/夜)', 'CNY'),
            (r'(?:价格|房价|房费|最低价|起价)[:\s]*[¥￥CN]*\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'CN¥\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'[¥￥]\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'CNY\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'([\d,]+(?:\.\d{2})?)\s*(?:元|人民币|yuan|Yuan)', 'CNY'),
            (r'人民币\s*([\d,]+(?:\.\d{2})?)', 'CNY'),
            (r'([\d,]+)\s*元/晚', 'CNY'),
            (r'([\d,]+(?:\.\d{2})?)\s*起', 'CNY'),
            (r'RMB\s*([\d,]+(?:\.\d{2})?)', 'CNY'),

            # === USD (US Dollar) patterns ===
            (r'per\s*night[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:/night|per\s*night)', 'USD'),
            (r'(?:price|rate|nightly)[:\s]*\$\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'\$\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'USD\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'from\s*\$?\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'starting\s*at\s*\$?\s*([\d,]+(?:\.\d{2})?)', 'USD'),
            (r'best\s*price[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)', 'USD'),

            # === EUR (Euro) patterns ===
            (r'€\s*([\d,]+(?:\.\d{2})?)', 'EUR'),
            (r'EUR\s*([\d,]+(?:\.\d{2})?)', 'EUR'),

            # === GBP (British Pound) patterns ===
            (r'£\s*([\d,]+(?:\.\d{2})?)', 'GBP'),
            (r'GBP\s*([\d,]+(?:\.\d{2})?)', 'GBP'),

            # === Generic number with currency suffix ===
            (r'([\d,]+(?:\.\d{2})?)\s*(?:HKD|TWD|CNY|USD|EUR|GBP)', 'CNY'),
        ]

        for i, (pattern, currency) in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                logger.debug(f"[Tavily Extract] Pattern #{i+1} matched: {pattern[:30]}... -> raw={match.group(0)}, value={price_str}")
                try:
                    price = float(price_str)
                    # Filter out unreasonable prices (< 10 or > 100000)
                    # Relaxed from 50-50000 to 10-100000 to support more currencies
                    if 10 <= price <= 100000:
                        logger.info(f"[Tavily Extract] ✓ Price found: {price} {currency} (pattern: {pattern[:40]}...)")
                        return price, currency
                    else:
                        logger.debug(f"[Tavily Extract] ✗ Price {price} out of range (10-100000), skipping")
                except ValueError as e:
                    logger.debug(f"[Tavily Extract] ✗ Failed to parse '{price_str}': {e}")
                    continue

        logger.debug("[Tavily Extract] No price pattern matched in text")
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
            'hotels': 7,
            'priceline': 8,
            'hotwire': 9
        }

        def sort_key(item):
            has_price = 0 if item.get('price') else 1
            priority = platform_priority.get(item.get('platform'), 99)
            return (has_price, priority)

        return sorted(results, key=sort_key)

    @staticmethod
    def normalize_for_comparison(tavily_data: Dict) -> List[Dict]:
        """
        Normalize Tavily results for comparison display.

        Args:
            tavily_data: Raw Tavily search results

        Returns:
            List of normalized comparison items
        """
        if not tavily_data or not tavily_data.get('results'):
            logger.debug("[Tavily Normalize] No results to normalize")
            return []

        raw_results = tavily_data.get('results', [])
        logger.info(f"[Tavily Normalize] Processing {len(raw_results)} raw results")

        # For each platform, select the best result (prefer ones with price)
        platform_best = {}
        for idx, item in enumerate(raw_results):
            platform = item.get('platform')
            if not platform:
                logger.debug(f"[Tavily Normalize] Skipping result #{idx+1}: no platform identified")
                continue

            if platform not in platform_best:
                # First result for this platform
                platform_best[platform] = item
                logger.debug(f"[Tavily Normalize] Platform {platform}: first result (price={item.get('price')})")
            elif item.get('price') and not platform_best[platform].get('price'):
                # New result has price, old one doesn't -> replace
                old_price = platform_best[platform].get('price')
                platform_best[platform] = item
                logger.debug(f"[Tavily Normalize] Platform {platform}: replaced (old_price={old_price}, new_price={item.get('price')})")

        logger.info(f"[Tavily Normalize] Found {len(platform_best)} unique platforms: {list(platform_best.keys())}")

        normalized = []
        for item in platform_best.values():
            normalized.append({
                'platform': item.get('platform'),
                'platform_name': item.get('platform_name', item.get('platform')),
                'icon': item.get('icon', 'bi-link'),
                'price': item.get('price'),
                'currency': item.get('currency', 'CNY'),
                'url': item.get('url'),
                'title': item.get('title', ''),
                'is_external': True  # Flag to identify external platforms
            })

        # Sort: platforms with prices first, then alphabetically by platform name
        normalized.sort(key=lambda x: (0 if x.get('price') else 1, x.get('platform_name', '')))

        # Log final normalized results
        prices_found = sum(1 for n in normalized if n.get('price'))
        logger.info(f"[Tavily Normalize] Final: {len(normalized)} platforms, {prices_found} with prices")
        for n in normalized:
            status = "✓" if n.get('price') else "✗"
            logger.debug(f"[Tavily Normalize]   {status} {n.get('platform_name')}: {n.get('price') or 'No price'}")

        return normalized
