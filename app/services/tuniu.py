"""
Tuniu MCP Service
Provides hotel search, detail, and booking functionality via Tuniu MCP API
"""
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from flask import current_app

logger = logging.getLogger(__name__)


class TuniuError(Exception):
    """Exception raised for Tuniu MCP errors."""
    pass


class TuniuService:
    """Service wrapper for Tuniu MCP API commands."""

    def __init__(self, api_key: Optional[str] = None, mcp_url: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key
        self.mcp_url = mcp_url
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
        if self.mcp_url:
            return self.mcp_url
        try:
            return current_app.config.get('TUNIU_MCP_URL', 'https://openapi.tuniu.cn/mcp/hotel')
        except RuntimeError:
            import os
            return os.environ.get('TUNIU_MCP_URL', 'https://openapi.tuniu.cn/mcp/hotel')

    def _call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Call a Tuniu MCP tool via HTTP request.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments

        Returns:
            Parsed JSON response

        Raises:
            TuniuError: If the request fails or returns an error
        """
        api_key = self._get_api_key()
        mcp_url = self._get_mcp_url()

        if not api_key:
            raise TuniuError("Tuniu API key not configured. Please set TUNIU_API_KEY environment variable.")

        # Build JSON-RPC 2.0 request
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "apiKey": api_key
        }

        logger.info(f"Calling Tuniu MCP tool: {tool_name}")

        try:
            response = requests.post(
                mcp_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise TuniuError(f"Tuniu API error: HTTP {response.status_code}")

            result = response.json()

            # Check for JSON-RPC error
            if 'error' in result:
                error_msg = result['error'].get('message', 'Unknown error')
                raise TuniuError(f"Tuniu API error: {error_msg}")

            # Extract content from MCP response
            content = result.get('result', {}).get('content', [])
            if content and len(content) > 0:
                text_content = content[0].get('text', '{}')
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    return {"raw": text_content}

            return result.get('result', {})

        except requests.Timeout:
            raise TuniuError(f"Tuniu API request timed out after {self.timeout} seconds")
        except requests.RequestException as e:
            raise TuniuError(f"Tuniu API request failed: {str(e)}")

    def search_hotels(
        self,
        city_name: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2,
        child_count: int = 0,
        keyword: Optional[str] = None,
        page_num: int = 1,
        query_id: Optional[str] = None
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
            page_num: Page number for pagination (default: 1)
            query_id: Query ID for pagination (required for pages > 1)

        Returns:
            Search results with hotel list and pagination info
        """
        arguments = {
            "cityName": city_name,
            "checkIn": check_in,
            "checkOut": check_out,
            "adultCount": adult_count,
            "childCount": child_count,
            "pageNum": page_num
        }

        if keyword:
            arguments["keyword"] = keyword
        if query_id:
            arguments["queryId"] = query_id

        return self._call_tool("tuniu_hotel_search", arguments)

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
            "hotelId": hotel_id,
            "checkIn": check_in,
            "checkOut": check_out,
            "adultCount": adult_count,
            "childCount": child_count
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
            "hotelId": hotel_id,
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

        Args:
            raw_hotel: Raw hotel dict from API
            provider: Provider name

        Returns:
            Normalized hotel dict
        """
        # Handle nested price object
        price_obj = raw_hotel.get('price', {})
        price_per_night = None
        currency = 'CNY'

        if price_obj and isinstance(price_obj, dict):
            price_per_night = price_obj.get('lowestPrice') or price_obj.get('price')
            currency = price_obj.get('currency', 'CNY')
        elif raw_hotel.get('price'):
            price_per_night = raw_hotel.get('price')
            currency = raw_hotel.get('currency', 'CNY')

        return {
            'hotel_id': str(raw_hotel.get('hotelId') or raw_hotel.get('hotel_id', '')),
            'name': raw_hotel.get('name') or raw_hotel.get('hotelName', ''),
            'address': raw_hotel.get('address', ''),
            'star_rating': raw_hotel.get('starRating') or raw_hotel.get('star_rating'),
            'rating': raw_hotel.get('rating') or raw_hotel.get('userRating') or raw_hotel.get('commentScore'),
            'price_per_night': price_per_night,
            'currency': currency,
            'image_url': raw_hotel.get('imageUrl') or raw_hotel.get('image_url') or raw_hotel.get('mainImage', ''),
            'provider': provider,
            # Tuniu specific fields
            'brand_name': raw_hotel.get('brandName'),
            'business': raw_hotel.get('business'),
            'comment_digest': raw_hotel.get('commentDigest')
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
        hotels = []
        raw_hotels = response.get('hotelList') or response.get('hotels') or response.get('data', [])

        if isinstance(raw_hotels, list):
            for hotel in raw_hotels:
                normalized = TuniuService.normalize_hotel(hotel)
                hotels.append(normalized)

        return {
            'hotels': hotels,
            'total': response.get('totalCount') or len(hotels),
            'query_id': response.get('queryId'),  # For pagination
            'page_num': response.get('pageNum', 1),
            'has_more': response.get('hasMore', False)
        }

    @staticmethod
    def normalize_hotel_detail(raw_detail: Dict, provider: str = "tuniu") -> Dict:
        """
        Normalize raw hotel detail data from Tuniu API to standard format.

        Args:
            raw_detail: Raw hotel detail dict from API
            provider: Provider name

        Returns:
            Normalized hotel detail dict
        """
        # Start with basic hotel normalization
        normalized = TuniuService.normalize_hotel(raw_detail, provider)

        # Add detail-specific fields
        normalized.update({
            'description': raw_detail.get('description') or raw_detail.get('introduction', ''),
            'images': raw_detail.get('images') or raw_detail.get('imageList', []),
            'amenities': raw_detail.get('amenities') or raw_detail.get('hotelAmenities', []),
            'room_plans': TuniuService._normalize_room_plans(
                raw_detail.get('roomPlans') or raw_detail.get('roomList', [])
            ),
            # Tuniu specific fields for booking
            'pre_book_param': raw_detail.get('preBookParam')
        })

        return normalized

    @staticmethod
    def _normalize_room_plans(raw_plans: List) -> List[Dict]:
        """Normalize room plans to standard format."""
        plans = []
        for plan in raw_plans:
            normalized_plan = {
                'room_id': plan.get('roomId') or plan.get('room_id', ''),
                'name': plan.get('name') or plan.get('roomName', ''),
                'description': plan.get('description', ''),
                'price': plan.get('price') or plan.get('pricePerNight'),
                'currency': plan.get('currency', 'CNY'),
                'available': plan.get('available', True) or plan.get('canBook', True),
                'amenities': plan.get('amenities', []),
                # Tuniu specific fields for booking
                'pre_book_param': plan.get('preBookParam'),
                'room_count': plan.get('roomCount', 1)
            }
            plans.append(normalized_plan)
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
