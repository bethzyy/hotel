"""
Hotel Provider Interface
Unified interface for multiple MCP providers (RollingGo, Tuniu)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from flask import current_app

from app.services.rollinggo import RollingGoService, RollingGoError
from app.services.tuniu import TuniuService, TuniuError


class HotelProviderError(Exception):
    """Exception raised for hotel provider errors."""
    pass


class HotelProvider(ABC):
    """Abstract base class for hotel providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def supports_booking(self) -> bool:
        """Whether this provider supports booking."""
        pass

    @property
    @abstractmethod
    def supports_pagination(self) -> bool:
        """Whether this provider supports pagination."""
        pass

    @abstractmethod
    def search_hotels(self, **kwargs) -> Dict:
        """Search for hotels."""
        pass

    @abstractmethod
    def get_hotel_detail(self, hotel_id: str, **kwargs) -> Dict:
        """Get hotel detail."""
        pass

    @abstractmethod
    def create_order(self, **kwargs) -> Dict:
        """Create a booking order (if supported)."""
        pass


class RollingGoProvider(HotelProvider):
    """RollingGo CLI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        self._service = RollingGoService(api_key=api_key, timeout=timeout)

    @property
    def name(self) -> str:
        return "rollinggo"

    @property
    def supports_booking(self) -> bool:
        return False

    @property
    def supports_pagination(self) -> bool:
        return False

    def search_hotels(
        self,
        query: str,
        place: str,
        place_type: str,
        check_in_date: Optional[str] = None,
        stay_nights: Optional[int] = None,
        adult_count: int = 2,
        child_count: int = 0,
        child_ages: Optional[List[int]] = None,
        star_ratings: Optional[str] = None,
        max_price: Optional[float] = None,
        distance: Optional[int] = None,
        required_tags: Optional[List[str]] = None,
        preferred_tags: Optional[List[str]] = None,
        size: int = 20,
        country_code: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """Search for hotels using RollingGo CLI."""
        try:
            result = self._service.search_hotels(
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

            # Normalize response
            hotels = []
            raw_hotels = (
                result.get('hotelInformationList') or
                result.get('hotels') or
                result.get('data') or
                []
            )
            if isinstance(raw_hotels, list):
                for hotel in raw_hotels:
                    normalized = RollingGoService.normalize_hotel(hotel)
                    normalized['provider'] = 'rollinggo'
                    hotels.append(normalized)

            return {
                'hotels': hotels,
                'total': len(hotels),
                'query': query,
                'place': place,
                'has_more': False,
                'query_id': None,
                'page_num': 1
            }

        except RollingGoError as e:
            raise HotelProviderError(f"RollingGo error: {str(e)}")

    def get_hotel_detail(
        self,
        hotel_id: str,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        adult_count: int = 2,
        child_count: int = 0,
        child_ages: Optional[List[int]] = None,
        room_count: int = 1,
        currency: str = 'CNY',
        **kwargs
    ) -> Dict:
        """Get hotel detail using RollingGo CLI."""
        try:
            result = self._service.get_hotel_detail(
                hotel_id=hotel_id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                adult_count=adult_count,
                child_count=child_count,
                child_ages=child_ages,
                room_count=room_count,
                currency=currency
            )

            normalized = RollingGoService.normalize_hotel_detail(result)
            normalized['provider'] = 'rollinggo'
            normalized['supports_booking'] = False
            return normalized

        except RollingGoError as e:
            raise HotelProviderError(f"RollingGo error: {str(e)}")

    def create_order(self, **kwargs) -> Dict:
        """RollingGo does not support booking."""
        raise HotelProviderError("RollingGo provider does not support booking. Please use Tuniu provider for booking.")


class TuniuProvider(HotelProvider):
    """Tuniu MCP provider implementation."""

    def __init__(self, api_key: Optional[str] = None, mcp_url: Optional[str] = None, timeout: int = 60):
        self._service = TuniuService(api_key=api_key, mcp_url=mcp_url, timeout=timeout)

    @property
    def name(self) -> str:
        return "tuniu"

    @property
    def supports_booking(self) -> bool:
        return True

    @property
    def supports_pagination(self) -> bool:
        return True

    def search_hotels(
        self,
        city_name: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2,
        child_count: int = 0,
        keyword: Optional[str] = None,
        page_num: int = 1,
        query_id: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """Search for hotels using Tuniu MCP."""
        try:
            result = self._service.search_hotels(
                city_name=city_name,
                check_in=check_in,
                check_out=check_out,
                adult_count=adult_count,
                child_count=child_count,
                keyword=keyword,
                page_num=page_num,
                query_id=query_id
            )

            normalized = TuniuService.normalize_search_response(result)

            # Add provider info to each hotel
            for hotel in normalized['hotels']:
                hotel['provider'] = 'tuniu'

            return normalized

        except TuniuError as e:
            raise HotelProviderError(f"Tuniu error: {str(e)}")

    def get_hotel_detail(
        self,
        hotel_id: str,
        check_in: str,
        check_out: str,
        adult_count: int = 2,
        child_count: int = 0,
        **kwargs
    ) -> Dict:
        """Get hotel detail using Tuniu MCP."""
        try:
            result = self._service.get_hotel_detail(
                hotel_id=hotel_id,
                check_in=check_in,
                check_out=check_out,
                adult_count=adult_count,
                child_count=child_count
            )

            normalized = TuniuService.normalize_hotel_detail(result)
            normalized['provider'] = 'tuniu'
            normalized['supports_booking'] = True
            return normalized

        except TuniuError as e:
            raise HotelProviderError(f"Tuniu error: {str(e)}")

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
        contact_phone: str,
        **kwargs
    ) -> Dict:
        """Create a booking order using Tuniu MCP."""
        try:
            result = self._service.create_order(
                hotel_id=hotel_id,
                room_id=room_id,
                pre_book_param=pre_book_param,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                room_count=room_count,
                room_guests=room_guests,
                contact_name=contact_name,
                contact_phone=contact_phone
            )

            return TuniuService.normalize_order_response(result)

        except TuniuError as e:
            raise HotelProviderError(f"Tuniu error: {str(e)}")


def get_provider(provider_name: str = None) -> HotelProvider:
    """
    Get a hotel provider instance by name.

    Args:
        provider_name: Provider name ('rollinggo' or 'tuniu'). Defaults to config DEFAULT_PROVIDER.

    Returns:
        HotelProvider instance

    Raises:
        HotelProviderError: If provider is not found or not configured
    """
    if provider_name is None:
        try:
            provider_name = current_app.config.get('DEFAULT_PROVIDER', 'tuniu')
        except RuntimeError:
            provider_name = 'tuniu'

    if provider_name == 'rollinggo':
        try:
            api_key = current_app.config.get('ROLLINGGO_API_KEY')
            timeout = current_app.config.get('ROLLINGGO_TIMEOUT', 60)
        except RuntimeError:
            import os
            api_key = os.environ.get('AIGOHOTEL_API_KEY')
            timeout = 60
        return RollingGoProvider(api_key=api_key, timeout=timeout)

    elif provider_name == 'tuniu':
        try:
            api_key = current_app.config.get('TUNIU_API_KEY')
            mcp_url = current_app.config.get('TUNIU_MCP_URL')
            timeout = current_app.config.get('TUNIU_TIMEOUT', 60)
        except RuntimeError:
            import os
            api_key = os.environ.get('TUNIU_API_KEY')
            mcp_url = os.environ.get('TUNIU_MCP_URL')
            timeout = 60
        return TuniuProvider(api_key=api_key, mcp_url=mcp_url, timeout=timeout)

    else:
        raise HotelProviderError(f"Unknown provider: {provider_name}")


def get_available_providers() -> List[Dict]:
    """
    Get list of available providers with their capabilities.

    Returns:
        List of provider info dicts
    """
    try:
        providers_config = current_app.config.get('PROVIDERS', {})
    except RuntimeError:
        providers_config = {
            'rollinggo': {
                'name': 'RollingGo',
                'description': '全球酒店搜索',
                'supports_booking': False,
                'supports_pagination': False
            },
            'tuniu': {
                'name': '途牛 MCP',
                'description': '国内酒店搜索与预订',
                'supports_booking': True,
                'supports_pagination': True
            }
        }

    providers = []
    for key, config in providers_config.items():
        providers.append({
            'id': key,
            'name': config.get('name', key),
            'description': config.get('description', ''),
            'supports_booking': config.get('supports_booking', False),
            'supports_pagination': config.get('supports_pagination', False)
        })

    return providers
