"""
Tuniu MCP Service
Provides hotel search, detail, and booking functionality via Tuniu MCP API
Uses MCP streamable HTTP client (same as RollingGo)
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from flask import current_app

# MCP client imports
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logger = logging.getLogger(__name__)


class TuniuError(Exception):
    """Exception raised for Tuniu MCP errors."""
    pass


class TuniuService:
    """Service wrapper for Tuniu MCP API commands."""

    # Tuniu MCP API endpoint
    MCP_API_BASE = "https://openapi.tuniu.cn/mcp/hotel"

    def __init__(self, api_key: Optional[str] = None, mcp_url: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key
        self.mcp_url = mcp_url or self.MCP_API_BASE
        self.timeout = timeout

    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        if self.api_key:
            return self.api_key
        try:
            return current_app.config.get('TUNIU_API_KEY', '')
        except RuntimeError:
            import os
            return os.environ.get('TUNIU_API_KEY', '')

    def _get_mcp_url(self) -> str:
        """Get MCP URL from config or environment."""
        if self.mcp_url and self.mcp_url != self.MCP_API_BASE:
            return self.mcp_url
        try:
            return current_app.config.get('TUNIU_MCP_URL', self.MCP_API_BASE)
        except RuntimeError:
            import os
            return os.environ.get('TUNIU_MCP_URL', self.MCP_API_BASE)

    async def _call_mcp_tool_async(self, tool_name: str, arguments: Dict) -> Optional[Dict]:
        """
        Async: Call Tuniu MCP tool via streamable HTTP client.

        Args:
            tool_name: MCP tool name (e.g., tuniu_hotel_search)
            arguments: Tool arguments

        Returns:
            Parsed JSON response or None on failure
        """
        api_key = self._get_api_key()
        mcp_url = self._get_mcp_url()

        if not api_key:
            raise TuniuError("Tuniu API key not configured. Please set TUNIU_API_KEY environment variable.")

        try:
            logger.info(f"Calling Tuniu MCP tool via streamable_http: {tool_name}")
            logger.debug(f"MCP URL: {mcp_url}")
            logger.debug(f"Arguments: {arguments}")

            # Create httpx client with apiKey header
            import httpx
            http_client = httpx.AsyncClient(
                headers={
                    "apiKey": api_key,
                },
                timeout=httpx.Timeout(60.0, read=300.0)
            )

            async with http_client:
                async with streamable_http_client(
                    mcp_url,
                    http_client=http_client
                ) as (read_stream, write_stream, _):
                    async with ClientSession(read_stream, write_stream) as session:
                        # Initialize session
                        await session.initialize()

                        # Call tool
                        result = await session.call_tool(tool_name, arguments)

                        logger.debug(f"MCP result isError: {result.isError}")

                        if result.isError:
                            error_text = ""
                            for content in result.content:
                                if hasattr(content, 'type') and content.type == "text":
                                    error_text = content.text
                            logger.error(f"Tuniu MCP tool error: {error_text}")
                            raise TuniuError(f"Tuniu API error: {error_text}")

                        # Parse response content
                        for content in result.content:
                            if hasattr(content, 'type') and content.type == "text":
                                try:
                                    data = json.loads(content.text)
                                    logger.debug(f"Tuniu MCP response parsed successfully")
                                    return data
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse Tuniu response: {e}")
                                    return {"raw": content.text}

                        logger.warning("No text content in Tuniu MCP response")
                        return None

        except TuniuError:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Tuniu MCP call failed: {e}")
            logger.debug(traceback.format_exc())
            raise TuniuError(f"Tuniu API request failed: {str(e)}")

    def _call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Synchronous wrapper for MCP tool call.

        Args:
            tool_name: MCP tool name
            arguments: Tool arguments

        Returns:
            Parsed JSON response

        Raises:
            TuniuError: If the request fails
        """
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._call_mcp_tool_async(tool_name, arguments)
                    )
                    return future.result(timeout=self.timeout)

            except TuniuError:
                raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Tuniu MCP call attempt {attempt + 1} failed, retrying: {e}")
                    import time
                    time.sleep(1)
                else:
                    logger.error(f"Failed to run Tuniu MCP call after {max_retries + 1} attempts: {e}")
                    raise TuniuError(f"Tuniu API call failed: {str(e)}")

    def search_hotels(
        self,
        city_name: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2,
        child_count: int = 0,
        keyword: Optional[str] = None,
        poi_name: Optional[str] = None,
        page_num: int = 1,
        query_id: Optional[str] = None,
        max_pages: int = 3
    ) -> Dict:
        """
        Search for hotels using Tuniu MCP.

        Args:
            city_name: City name (e.g., "北京", "上海")
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adult_count: Number of adults (default: 2)
            child_count: Number of children (default: 0)
            keyword: Hotel name or brand keyword (optional)
            poi_name: POI/landmark name for area-based search (e.g., "香山", "外滩")
            page_num: Page number for pagination (default: 1)
            query_id: Query ID for pagination (required for pages > 1)
            max_pages: Max pages to fetch (default: 3, each page has ~8 hotels)

        Returns:
            Search results with hotel list and pagination info
        """
        # Build arguments for first page
        arguments = {
            "cityName": city_name,
            "checkIn": check_in,
            "checkOut": check_out,
            "adultNum": adult_count,
            "childNum": child_count,
            "pageNum": page_num
        }

        if keyword:
            arguments["keyword"] = keyword
        if poi_name:
            arguments["poiName"] = poi_name
        if query_id:
            arguments["queryId"] = query_id

        result = self._call_tool("tuniu_hotel_search", arguments)

        # Multi-page fetch: auto-fetch additional pages
        total_pages = result.get('totalPageNum') or 1
        result_query_id = result.get('queryId')

        if max_pages > 1 and result_query_id and total_pages > page_num:
            for p in range(page_num + 1, min(total_pages + 1, page_num + max_pages)):
                try:
                    next_args = {
                        "queryId": result_query_id,
                        "pageNum": p
                    }
                    next_result = self._call_tool("tuniu_hotel_search", next_args)

                    # Merge hotel lists — normalize to 'hotelList' key
                    next_hotels = next_result.get('hotelList') or next_result.get('hotels') or next_result.get('data') or []
                    curr_hotels = result.get('hotelList') or result.get('hotels') or result.get('data') or []
                    result['hotelList'] = curr_hotels  # Ensure normalized key
                    curr_hotels.extend(next_hotels)

                    # Update pagination info
                    result['currentPageNum'] = p
                    logger.info(f"[Tuniu] Fetched page {p}/{total_pages}, total hotels: {len(curr_hotels)}")
                except TuniuError as e:
                    logger.warning(f"[Tuniu] Failed to fetch page {p}: {e}")
                    break

        return result

    def get_hotel_detail(
        self,
        hotel_id: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2,
        child_count: int = 0
    ) -> Dict:
        """
        Get detailed information for a hotel.

        Args:
            hotel_id: Hotel ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adult_count: Number of adults (default: 2)
            child_count: Number of children (default: 0)

        Returns:
            Hotel detail with room plans and preBookParam
        """
        arguments = {
            "hotelId": int(hotel_id),
            "checkIn": check_in,
            "checkOut": check_out,
            "adultNum": adult_count,
            "childNum": child_count
        }

        return self._call_tool("tuniu_hotel_detail", arguments)

    def create_order(
        self,
        hotel_id: str,
        room_id: str,
        pre_book_param: str,
        check_in_date: str,
        check_out_date: str,
        room_count: int,
        room_guests: List[Dict],
        contact_name: str,
        contact_phone: str
    ) -> Dict:
        """
        Create a hotel booking order.

        Args:
            hotel_id: Hotel ID
            room_id: Room type ID
            pre_book_param: Pre-booking parameter from hotel detail
            check_in_date: Check-in date (YYYY-MM-DD)
            check_out_date: Check-out date (YYYY-MM-DD)
            room_count: Number of rooms
            room_guests: List of room guest info [{"guests": [{"firstName": "x", "lastName": "y"}]}]
            contact_name: Contact person name
            contact_phone: Contact person phone

        Returns:
            Order result with order_id, confirmation_number, payment_url
        """
        arguments = {
            "hotelId": str(hotel_id),
            "roomId": room_id,
            "preBookParam": pre_book_param,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "roomCount": room_count,
            "roomGuests": room_guests,
            "contactName": contact_name,
            "contactPhone": contact_phone
        }

        return self._call_tool("tuniu_hotel_create_order", arguments)

    @staticmethod
    def normalize_hotel(raw_hotel: Dict, provider: str = "tuniu") -> Dict:
        """
        Normalize raw hotel data from Tuniu API to standard format.
        """
        # Handle price: Tuniu returns lowestPrice as direct field, or nested in price object
        price_obj = raw_hotel.get('price')
        price_per_night = None
        currency = 'CNY'

        if price_obj and isinstance(price_obj, dict):
            price_per_night = price_obj.get('lowestPrice') or price_obj.get('price')
            currency = price_obj.get('currency', 'CNY')
        elif raw_hotel.get('lowestPrice'):
            price_per_night = raw_hotel.get('lowestPrice')
        elif raw_hotel.get('price'):
            price_per_night = raw_hotel.get('price')

        # Handle star rating: Tuniu returns starName (string) and/or numeric starRating
        star_rating = raw_hotel.get('starRating') or raw_hotel.get('star_rating')
        star_name = raw_hotel.get('starName', '')
        if not star_rating and star_name:
            # Map common Tuniu starName values to numeric
            star_map = {
                '经济型': 2.0, '舒适型': 3.0, '高档型': 4.0,
                '豪华型': 5.0, '二星级': 2.0, '二星及以下': 1.5,
                '三星级': 3.0, '四星级': 4.0, '五星级': 5.0,
            }
            star_rating = star_map.get(star_name)

        return {
            'hotel_id': str(raw_hotel.get('hotelId') or raw_hotel.get('hotel_id', '')),
            'name': raw_hotel.get('name') or raw_hotel.get('hotelName', ''),
            'address': raw_hotel.get('address', ''),
            'star_rating': star_rating,
            'star_name': star_name,
            'rating': raw_hotel.get('rating') or raw_hotel.get('userRating') or raw_hotel.get('commentScore'),
            'price_per_night': price_per_night,
            'currency': currency,
            'image_url': raw_hotel.get('imageUrl') or raw_hotel.get('image_url') or raw_hotel.get('mainImage', '') or raw_hotel.get('firstPic', ''),
            'provider': provider,
            # Tuniu specific fields
            'brand_name': raw_hotel.get('brandName'),
            'business': raw_hotel.get('business'),
            'comment_digest': raw_hotel.get('commentDigest'),
            'meal': raw_hotel.get('meal'),
            'refund': raw_hotel.get('refund'),
            'room_name': raw_hotel.get('roomName'),
        }

    @staticmethod
    def normalize_search_response(response: Dict) -> Dict:
        """
        Normalize Tuniu search response to standard format.

        Args:
            response: Raw API response

        Returns:
            Normalized response with hotels list and pagination info
        """
        raw_hotels = response.get('hotelList') or response.get('hotels') or response.get('data', [])
        hotels = []

        if isinstance(raw_hotels, list):
            for hotel in raw_hotels:
                normalized = TuniuService.normalize_hotel(hotel)
                hotels.append(normalized)

        # Tuniu returns totalPageNum/currentPageNum or totalCount/pageNum
        current_page = response.get('currentPageNum') or response.get('pageNum', 1)
        total_pages = response.get('totalPageNum') or 0
        total_count = response.get('totalCount') or len(hotels)

        return {
            'hotels': hotels,
            'total': total_count,
            'query_id': response.get('queryId'),  # For pagination
            'page_num': current_page,
            'has_more': total_pages > current_page
        }

    @staticmethod
    def normalize_hotel_detail(raw_detail: Dict, provider: str = "tuniu") -> Dict:
        """
        Normalize raw hotel detail data from Tuniu API to standard format.

        Tuniu detail returns:
        { hotelId, hotelName, hotelNameEn, starName, firstPic, cityName, cityCode,
          business, commentScore, policies: {checkInTime, checkOutTime, cancelPolicy},
          roomTypes: [{ roomTypeId, roomTypeName, bedType, maxOccupancy, roomSize, floor,
                        images: [], ratePlans: [{ ratePlanName, vendorRatePlanId, rmbPrices,
                        preBookParam, mealText, cancelDesc, stock }] }],
          reviews: {score, count} }
        """
        normalized = TuniuService.normalize_hotel(raw_detail, provider)

        # Compute lowest price from room types
        room_types = raw_detail.get('roomTypes') or raw_detail.get('roomList') or []
        lowest_price = None
        for rt in room_types:
            for rp in rt.get('ratePlans', []):
                try:
                    p = float(rp.get('rmbPrices', 0))
                    if p and (lowest_price is None or p < lowest_price):
                        lowest_price = p
                except (ValueError, TypeError):
                    pass

        if lowest_price and not normalized.get('price_per_night'):
            normalized['price_per_night'] = lowest_price

        # Policies
        raw_policies = raw_detail.get('policies', {})

        # Room images from first room type (for gallery)
        all_images = []
        for rt in room_types:
            for img in (rt.get('images') or []):
                if img not in all_images:
                    all_images.append(img)
        if raw_detail.get('firstPic') and raw_detail['firstPic'] not in all_images:
            all_images.insert(0, raw_detail['firstPic'])

        normalized.update({
            'description': raw_detail.get('description') or raw_detail.get('introduction', ''),
            'images': all_images if all_images else [raw_detail.get('firstPic', '')],
            'amenities': raw_detail.get('amenities') or raw_detail.get('hotelAmenities', []),
            'room_plans': TuniuService._normalize_room_plans(room_types),
            # Policies
            'policies': {
                'check_in_time': raw_policies.get('checkInTime', ''),
                'check_out_time': raw_policies.get('checkOutTime', ''),
                'cancel_policy': raw_policies.get('cancelPolicy', ''),
            } if raw_policies else None,
            # Reviews
            'reviews': raw_detail.get('reviews'),
            # Extra fields
            'hotel_name_en': raw_detail.get('hotelNameEn', ''),
        })

        return normalized

    @staticmethod
    def _normalize_room_plans(raw_room_types: List) -> List[Dict]:
        """
        Normalize Tuniu roomTypes + ratePlans into flat RoomPlan list.

        Tuniu structure: roomTypes[].ratePlans[] — one room type has multiple rate plans.
        We flatten them so each rate plan becomes a RoomPlan.
        Frontend groups by room_type_id for display.
        """
        plans = []
        if not raw_room_types:
            return plans

        for rt in raw_room_types:
            room_type_id = str(rt.get('roomTypeId', ''))
            room_name = rt.get('roomTypeName', '')
            bed_type = rt.get('bedType', '')
            max_occupancy = rt.get('maxOccupancy')
            room_size = rt.get('roomSize')
            floor = rt.get('floor', '')
            has_window = rt.get('hasWindow')
            room_images = rt.get('images', [])

            for rp in rt.get('ratePlans', []):
                try:
                    price = float(rp.get('rmbPrices', 0)) if rp.get('rmbPrices') else None
                except (ValueError, TypeError):
                    price = None

                plan = {
                    'room_id': room_type_id,
                    'room_type_id': room_type_id,
                    'room_name': room_name,
                    'bed_type': bed_type,
                    'room_size': f"{room_size}㎡" if room_size else None,
                    'max_occupancy': max_occupancy,
                    'floor': floor,
                    'has_window': has_window,
                    'room_images': room_images,
                    # Rate plan info
                    'rate_plan_name': rp.get('ratePlanName', ''),
                    'rate_plan_id': rp.get('vendorRatePlanId', ''),
                    'price': price,
                    'currency': 'CNY',
                    'breakfast': rp.get('mealText', ''),
                    'cancel_policy': rp.get('cancelDesc', ''),
                    'available': rp.get('stock') is None or (rp.get('stock') or 0) > 0,
                    # For booking
                    'pre_book_param': rp.get('preBookParam'),
                    'room_count': 1,
                }
                plans.append(plan)

        return plans

    @staticmethod
    def normalize_order_response(response: Dict) -> Dict:
        """
        Normalize Tuniu order response to standard format.

        Args:
            response: Raw API response

        Returns:
            Normalized response with order details
        """
        return {
            'success': response.get('success', True),
            'order_id': response.get('orderId') or response.get('order_id'),
            'confirmation_number': response.get('confirmationNumber') or response.get('confirmNo'),
            'payment_url': response.get('paymentUrl') or response.get('payUrl'),
            'error': response.get('error') or response.get('errorMsg')
        }
