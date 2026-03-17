"""
RollingGo CLI wrapper service
Encapsulates hotel search, detail, and tags commands
"""
import asyncio
import json
import subprocess
import logging
from typing import Dict, List, Optional, Any
from flask import current_app

# MCP client imports
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logger = logging.getLogger(__name__)


class RollingGoError(Exception):
    """Exception raised for RollingGo CLI errors."""
    pass


class RollingGoService:
    """Service wrapper for RollingGo CLI commands."""

    # MCP API 端点（用于直接获取 bookingUrl）
    MCP_API_BASE = "https://mcp.aigohotel.com/mcp"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout

    async def _call_mcp_tool_async(self, tool_name: str, arguments: Dict) -> Optional[Dict]:
        """
        异步调用 MCP 工具获取原始数据（包含 bookingUrl）

        Args:
            tool_name: MCP 工具名称（如 search_hotels, hotel_detail）
            arguments: 工具参数

        Returns:
            解析后的 JSON 数据，失败返回 None
        """
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("No API key available for MCP API call")
            return None

        try:
            logger.info(f"Calling MCP tool via streamable_http: {tool_name}")
            logger.debug(f"MCP API URL: {self.MCP_API_BASE}")
            logger.debug(f"MCP arguments: {arguments}")

            # 创建带有 Authorization header 的 httpx 客户端
            import httpx
            http_client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=httpx.Timeout(60.0, read=300.0)  # 5 minutes read timeout
            )

            async with http_client:
                async with streamable_http_client(
                    self.MCP_API_BASE,
                    http_client=http_client
                ) as (read_stream, write_stream, _):
                    async with ClientSession(read_stream, write_stream) as session:
                        # 初始化会话
                        await session.initialize()

                        # 调用工具
                        result = await session.call_tool(tool_name, arguments)

                        logger.debug(f"MCP result isError: {result.isError}")
                        logger.debug(f"MCP result content count: {len(result.content) if result.content else 0}")

                        if result.isError:
                            logger.error(f"MCP tool error: {result.content}")
                            return None

                        # 解析返回内容
                        for content in result.content:
                            logger.debug(f"Content type: {getattr(content, 'type', 'unknown')}")
                            if hasattr(content, 'type') and content.type == "text":
                                try:
                                    data = json.loads(content.text)
                                    logger.debug(f"MCP response parsed successfully")
                                    return data
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse MCP response: {e}")
                                    logger.debug(f"Raw text: {content.text[:500] if content.text else 'empty'}")
                                    return None

                        logger.warning("No text content in MCP response")
                        return None

        except Exception as e:
            import traceback
            logger.error(f"MCP call failed: {e}")
            logger.debug(traceback.format_exc())
            return None

    def _call_mcp_tool(self, tool_name: str, arguments: Dict) -> Optional[Dict]:
        """
        同步包装器：调用 MCP 工具

        Args:
            tool_name: MCP 工具名称
            arguments: 工具参数

        Returns:
            解析后的 JSON 数据，失败返回 None
        """
        try:
            # 尝试获取现有事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果循环正在运行，使用线程池执行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._call_mcp_tool_async(tool_name, arguments)
                        )
                        return future.result(timeout=self.timeout)
            except RuntimeError:
                pass

            # 创建新的事件循环
            return asyncio.run(self._call_mcp_tool_async(tool_name, arguments))

        except Exception as e:
            logger.error(f"Failed to run MCP call: {e}")
            return None

    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        if self.api_key:
            return self.api_key
        try:
            return current_app.config.get('ROLLINGGO_API_KEY', '')
        except RuntimeError:
            # Outside of Flask context
            import os
            return os.environ.get('AIGOHOTEL_API_KEY', '')

    def _run_command(self, args: List[str]) -> Dict:
        """
        Execute RollingGo CLI command and return parsed JSON result.

        Args:
            args: Command arguments (not including 'npx rollinggo')

        Returns:
            Parsed JSON response

        Raises:
            RollingGoError: If command fails or returns error
        """
        # Build full command
        cmd = ['npx', 'rollinggo'] + args

        # Add API key if available
        api_key = self._get_api_key()
        if api_key:
            cmd.extend(['--api-key', api_key])

        logger.info(f"Executing RollingGo command: {' '.join(cmd[:3])}...")

        try:
            # Use shell=True on Windows for npx to be found
            import platform
            use_shell = platform.system() == 'Windows'

            if use_shell:
                # For shell mode, need to properly quote arguments
                import shlex
                # Use list2cmdline for Windows
                import subprocess as sp
                cmd_str = sp.list2cmdline(cmd)
            else:
                cmd_str = cmd

            result = subprocess.run(
                cmd_str,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                shell=use_shell
            )

            # Check exit code
            if result.returncode == 1:
                # HTTP or network failure
                error_msg = result.stderr.strip() or "Network error"
                raise RollingGoError(f"Network error: {error_msg}")
            elif result.returncode == 2:
                # CLI validation failure
                error_msg = result.stderr.strip() or "Validation error"
                raise RollingGoError(f"Validation error: {error_msg}")
            elif result.returncode != 0:
                error_msg = result.stderr.strip() or f"Unknown error (code {result.returncode})"
                raise RollingGoError(error_msg)

            # Parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise RollingGoError(f"Failed to parse response: {e}")

        except subprocess.TimeoutExpired:
            raise RollingGoError(f"Command timed out after {self.timeout} seconds")
        except FileNotFoundError:
            raise RollingGoError("RollingGo CLI not found. Please ensure npx is available.")

    def search_hotels(
        self,
        query: str,
        place: str,
        place_type: str,
        check_in_date: Optional[str] = None,
        stay_nights: Optional[int] = None,
        adult_count: Optional[int] = None,
        child_count: Optional[List[int]] = None,
        child_ages: Optional[List[int]] = None,
        star_ratings: Optional[str] = None,
        max_price: Optional[float] = None,
        distance: Optional[int] = None,
        required_tags: Optional[List[str]] = None,
        preferred_tags: Optional[List[str]] = None,
        size: Optional[int] = None,
        country_code: Optional[str] = None
    ) -> Dict:
        """
        Search for hotels using MCP API (with bookingUrl) or fallback to CLI.

        Args:
            query: Search query text
            place: Destination place name
            place_type: Type of place (attraction, city, etc.)
            check_in_date: Check-in date (YYYY-MM-DD)
            stay_nights: Number of nights
            adult_count: Number of adults
            child_count: Number of children
            child_ages: List of children's ages
            star_ratings: Star rating range (e.g., "4.0,5.0")
            max_price: Maximum price per night
            distance: Maximum distance in meters
            required_tags: Tags that must be present
            preferred_tags: Tags to prefer
            size: Number of results
            country_code: Country code (ISO2)

        Returns:
            Search results as dict with hotel list
        """
        # 首先尝试通过 MCP API 获取数据（包含 bookingUrl）
        result = self._search_hotels_via_api(
            query=query,
            place=place,
            place_type=place_type,
            check_in_date=check_in_date,
            stay_nights=stay_nights,
            adult_count=adult_count,
            star_ratings=star_ratings,
            max_price=max_price,
            distance=distance,
            required_tags=required_tags,
            preferred_tags=preferred_tags,
            size=size,
            country_code=country_code
        )

        if result:
            logger.info("Successfully fetched hotels via MCP API (with bookingUrl)")
            return result

        # 回退到 CLI
        logger.info("MCP API failed, falling back to CLI")
        return self._search_hotels_via_cli(
            query=query,
            place=place,
            place_type=place_type,
            check_in_date=check_in_date,
            stay_nights=stay_nights,
            adult_count=adult_count,
            child_count=child_count,
            child_ages=child_ages,
            star_ratings=star_ratings,
            max_price=max_price,
            distance=distance,
            required_tags=required_tags,
            preferred_tags=preferred_tags,
            size=size,
            country_code=country_code
        )

    def _search_hotels_via_cli(
        self,
        query: str,
        place: str,
        place_type: str,
        check_in_date: Optional[str] = None,
        stay_nights: Optional[int] = None,
        adult_count: Optional[int] = None,
        child_count: Optional[int] = None,
        child_ages: Optional[List[int]] = None,
        star_ratings: Optional[str] = None,
        max_price: Optional[float] = None,
        distance: Optional[int] = None,
        required_tags: Optional[List[str]] = None,
        preferred_tags: Optional[List[str]] = None,
        size: Optional[int] = None,
        country_code: Optional[str] = None
    ) -> Dict:
        """
        使用 CLI 搜索酒店
        """
        args = [
            'search-hotels',
            '--origin-query', query,
            '--place', place,
            '--place-type', place_type
        ]

        # Add optional parameters
        if check_in_date:
            args.extend(['--check-in-date', check_in_date])
        if stay_nights:
            args.extend(['--stay-nights', str(stay_nights)])
        if adult_count:
            args.extend(['--adult-count', str(adult_count)])
        # Note: --child-count and --child-age removed from RollingGo CLI v0.1.1+
        # Keeping function parameters for backward compatibility
        if star_ratings:
            args.extend(['--star-ratings', star_ratings])
        if max_price:
            args.extend(['--max-price-per-night', str(max_price)])
        if distance:
            args.extend(['--distance-in-meter', str(distance)])
        if size:
            args.extend(['--size', str(size)])
        if country_code:
            args.extend(['--country-code', country_code])

        # Add tag filters
        if required_tags:
            for tag in required_tags:
                args.extend(['--required-tag', tag])
        if preferred_tags:
            for tag in preferred_tags:
                args.extend(['--preferred-tag', tag])

        return self._run_command(args)

    def get_hotel_detail(
        self,
        hotel_id: Optional[str] = None,
        name: Optional[str] = None,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        adult_count: Optional[int] = None,
        child_count: Optional[int] = None,
        child_ages: Optional[List[int]] = None,
        room_count: Optional[int] = None,
        country_code: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Dict:
        """
        Get detailed information for a hotel using MCP API (with bookingUrl) or fallback to CLI.

        Args:
            hotel_id: Hotel ID (preferred)
            name: Hotel name (alternative to hotel_id)
            check_in_date: Check-in date (YYYY-MM-DD)
            check_out_date: Check-out date (YYYY-MM-DD)
            adult_count: Number of adults
            child_count: Number of children
            child_ages: List of children's ages
            room_count: Number of rooms
            country_code: Country code (ISO2)
            currency: Currency code (ISO4217)

        Returns:
            Hotel detail as dict
        """
        if not hotel_id and not name:
            raise RollingGoError("Either hotel_id or name must be provided")

        # 首先尝试通过 MCP API 获取数据（包含 bookingUrl）
        result = self._get_hotel_detail_via_api(
            hotel_id=hotel_id,
            name=name,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adult_count=adult_count,
            room_count=room_count,
            country_code=country_code,
            currency=currency
        )

        if result:
            logger.info("Successfully fetched hotel detail via MCP API (with bookingUrl)")
            return result

        # 回退到 CLI
        logger.info("MCP API failed, falling back to CLI")
        return self._get_hotel_detail_via_cli(
            hotel_id=hotel_id,
            name=name,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adult_count=adult_count,
            child_count=child_count,
            child_ages=child_ages,
            room_count=room_count,
            country_code=country_code,
            currency=currency
        )

    def _get_hotel_detail_via_api(
        self,
        hotel_id: Optional[str] = None,
        name: Optional[str] = None,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        adult_count: Optional[int] = None,
        room_count: Optional[int] = None,
        country_code: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Optional[Dict]:
        """
        通过 MCP 协议调用 API 获取酒店详情（获取 bookingUrl）

        Returns:
            API 响应数据，失败返回 None
        """
        params = {}

        if hotel_id:
            params['hotelId'] = hotel_id
        elif name:
            params['name'] = name
        else:
            return None

        if check_in_date:
            params['checkInDate'] = check_in_date
        if check_out_date:
            params['checkOutDate'] = check_out_date
        if adult_count:
            params['adultCount'] = adult_count
        if room_count:
            params['roomCount'] = room_count
        if country_code:
            params['countryCode'] = country_code
        if currency:
            params['currency'] = currency

        # 使用 camelCase 工具名称
        result = self._call_mcp_tool('getHotelDetail', params)
        return result

    def _search_hotels_via_api(
        self,
        query: str,
        place: str,
        place_type: str,
        check_in_date: Optional[str] = None,
        stay_nights: Optional[int] = None,
        adult_count: Optional[int] = None,
        star_ratings: Optional[str] = None,
        max_price: Optional[float] = None,
        distance: Optional[int] = None,
        required_tags: Optional[List[str]] = None,
        preferred_tags: Optional[List[str]] = None,
        size: Optional[int] = None,
        country_code: Optional[str] = None
    ) -> Optional[Dict]:
        """
        通过 MCP 协议调用 API 搜索酒店（获取 bookingUrl）

        Returns:
            API 响应数据，失败返回 None
        """
        params = {
            'originQuery': query,
            'place': place,
            'placeType': place_type
        }

        if check_in_date:
            params['checkInDate'] = check_in_date
        if stay_nights:
            params['stayNights'] = stay_nights
        if adult_count:
            params['adultCount'] = adult_count
        if star_ratings:
            params['starRatings'] = star_ratings
        if max_price:
            params['maxPricePerNight'] = max_price
        if distance:
            params['distanceInMeter'] = distance
        if size:
            params['size'] = size
        if country_code:
            params['countryCode'] = country_code
        if required_tags:
            params['requiredTags'] = required_tags
        if preferred_tags:
            params['preferredTags'] = preferred_tags

        # 使用 camelCase 工具名称
        result = self._call_mcp_tool('searchHotels', params)

        # 转换 MCP API 响应格式为 CLI 格式
        if result and 'hotelInformationList' in result:
            result['hotels'] = result.pop('hotelInformationList')

        return result

    def _get_hotel_detail_via_cli(
        self,
        hotel_id: Optional[str] = None,
        name: Optional[str] = None,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        adult_count: Optional[int] = None,
        child_count: Optional[int] = None,
        child_ages: Optional[List[int]] = None,
        room_count: Optional[int] = None,
        country_code: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Dict:
        """
        使用 CLI 获取酒店详情（回退方案）
        """
        args = ['hotel-detail']

        # Add identifier
        if hotel_id:
            args.extend(['--hotel-id', hotel_id])
        else:
            args.extend(['--name', name])

        # Add optional parameters
        if check_in_date:
            args.extend(['--check-in-date', check_in_date])
        if check_out_date:
            args.extend(['--check-out-date', check_out_date])
        if adult_count:
            args.extend(['--adult-count', str(adult_count)])
        # Note: --child-count and --child-age removed from RollingGo CLI v0.1.1+
        # Keeping function parameters for backward compatibility
        if room_count:
            args.extend(['--room-count', str(room_count)])
        if country_code:
            args.extend(['--country-code', country_code])
        if currency:
            args.extend(['--currency', currency])

        return self._run_command(args)

    def get_tags(self) -> List[str]:
        """
        Get list of available tags for filtering.

        Returns:
            List of tag strings
        """
        result = self._run_command(['hotel-tags'])

        # Handle different response formats
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'tags' in result:
            return result['tags']
        else:
            return []

    @staticmethod
    def normalize_hotel(raw_hotel: Dict) -> Dict:
        """
        Normalize raw hotel data from CLI or MCP API response to standard format.

        Args:
            raw_hotel: Raw hotel dict from CLI or MCP API

        Returns:
            Normalized hotel dict
        """
        # Handle nested price object
        price_obj = raw_hotel.get('price', {})
        price_per_night = None
        currency = 'CNY'
        if price_obj and isinstance(price_obj, dict):
            price_per_night = price_obj.get('lowestPrice')
            currency = price_obj.get('currency', 'CNY')
        elif raw_hotel.get('pricePerNight'):
            price_per_night = raw_hotel.get('pricePerNight')
            currency = raw_hotel.get('currency', 'CNY')

        return {
            'hotel_id': str(raw_hotel.get('hotelId') or raw_hotel.get('hotel_id', '')),
            'name': raw_hotel.get('name', ''),
            'address': raw_hotel.get('address', ''),
            'star_rating': raw_hotel.get('starRating') or raw_hotel.get('star_rating'),
            'rating': raw_hotel.get('score') or raw_hotel.get('rating') or raw_hotel.get('userRating'),  # MCP API uses 'score'
            'price_per_night': price_per_night,
            'currency': currency,
            'distance': raw_hotel.get('distanceInMeters') or raw_hotel.get('distanceInMeter') or raw_hotel.get('distance'),
            'tags': raw_hotel.get('tags', []),
            'image_url': raw_hotel.get('imageUrl') or raw_hotel.get('image_url'),
            'latitude': raw_hotel.get('latitude') or raw_hotel.get('lat'),
            'longitude': raw_hotel.get('longitude') or raw_hotel.get('lng'),
            'booking_url': raw_hotel.get('bookingUrl'),  # MCP API 返回的预订链接
            'description': raw_hotel.get('description', ''),  # MCP API 可能返回描述
            'brand': raw_hotel.get('brand'),  # MCP API 返回品牌
            'amenities': raw_hotel.get('hotelAmenities') or raw_hotel.get('amenities', []),  # MCP API 返回设施
        }

    @staticmethod
    def normalize_hotel_detail(raw_detail: Dict) -> Dict:
        """
        Normalize raw hotel detail data from CLI response to standard format.

        Args:
            raw_detail: Raw hotel detail dict from CLI

        Returns:
            Normalized hotel detail dict
        """
        # Start with basic hotel normalization
        normalized = RollingGoService.normalize_hotel(raw_detail)

        # Get amenities from either hotelAmenities or amenities
        amenities = raw_detail.get('hotelAmenities') or raw_detail.get('amenities', [])

        # Add detail-specific fields
        normalized.update({
            'description': raw_detail.get('description', ''),
            'images': raw_detail.get('images', []),
            'amenities': amenities,
            'room_plans': RollingGoService._normalize_room_plans(
                raw_detail.get('roomPlans') or raw_detail.get('room_plans', [])
            )
        })

        return normalized

    @staticmethod
    def _normalize_room_plans(raw_plans: List) -> List[Dict]:
        """Normalize room plans to standard format."""
        plans = []
        for plan in raw_plans:
            plans.append({
                'name': plan.get('name') or plan.get('roomName', ''),
                'description': plan.get('description', ''),
                'price': plan.get('price') or plan.get('pricePerNight'),
                'currency': plan.get('currency', 'CNY'),
                'available': plan.get('available', True),
                'amenities': plan.get('amenities', [])
            })
        return plans
