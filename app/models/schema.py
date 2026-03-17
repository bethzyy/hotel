"""
Pydantic models for request/response validation
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SearchRequest(BaseModel):
    """Hotel search request model."""
    query: str = Field(..., description="Search query text")
    place: str = Field(..., description="Destination place name")
    place_type: str = Field(..., description="Type of place (attraction, city, etc.)")
    check_in_date: Optional[str] = Field(None, description="Check-in date YYYY-MM-DD")
    stay_nights: int = Field(1, ge=1, le=30, description="Number of nights")
    adult_count: int = Field(2, ge=1, le=10, description="Number of adults")
    child_count: int = Field(0, ge=0, le=10, description="Number of children")
    child_ages: List[int] = Field(default_factory=list, description="Ages of children")
    star_ratings: Optional[str] = Field(None, description="Star rating range e.g. '4.0,5.0'")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price per night")
    distance: Optional[int] = Field(None, ge=0, description="Maximum distance in meters")
    required_tags: List[str] = Field(default_factory=list, description="Required tags")
    preferred_tags: List[str] = Field(default_factory=list, description="Preferred tags")
    size: int = Field(10, ge=1, le=50, description="Number of results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find hotels near Shanghai Disneyland",
                "place": "Shanghai Disneyland",
                "place_type": "attraction",
                "check_in_date": "2026-04-01",
                "stay_nights": 2,
                "adult_count": 2,
                "child_count": 0,
                "child_ages": [],
                "star_ratings": "4.0,5.0",
                "max_price": 1000,
                "distance": 5000,
                "required_tags": [],
                "preferred_tags": [],
                "size": 10
            }
        }


class Hotel(BaseModel):
    """Hotel summary model for search results."""
    hotel_id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    address: Optional[str] = Field(None, description="Hotel address")
    star_rating: Optional[float] = Field(None, description="Star rating")
    rating: Optional[float] = Field(None, description="User rating")
    price_per_night: Optional[float] = Field(None, description="Price per night")
    currency: Optional[str] = Field(None, description="Currency code")
    distance: Optional[int] = Field(None, description="Distance in meters")
    tags: List[str] = Field(default_factory=list, description="Hotel tags")
    image_url: Optional[str] = Field(None, description="Main image URL")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")


class RoomPlan(BaseModel):
    """Room plan model for hotel detail."""
    name: Optional[str] = Field(None, description="Room name")
    description: Optional[str] = Field(None, description="Room description")
    price: Optional[float] = Field(None, description="Price per night")
    currency: Optional[str] = Field(None, description="Currency code")
    available: bool = Field(True, description="Whether room is available")
    amenities: List[str] = Field(default_factory=list, description="Room amenities")


class HotelDetail(BaseModel):
    """Detailed hotel model."""
    hotel_id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    address: Optional[str] = Field(None, description="Hotel address")
    star_rating: Optional[float] = Field(None, description="Star rating")
    rating: Optional[float] = Field(None, description="User rating")
    price_per_night: Optional[float] = Field(None, description="Starting price per night")
    currency: Optional[str] = Field(None, description="Currency code")
    distance: Optional[int] = Field(None, description="Distance in meters")
    tags: List[str] = Field(default_factory=list, description="Hotel tags")
    image_url: Optional[str] = Field(None, description="Main image URL")
    images: List[str] = Field(default_factory=list, description="Gallery images")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    description: Optional[str] = Field(None, description="Hotel description")
    amenities: List[str] = Field(default_factory=list, description="Hotel amenities")
    room_plans: List[RoomPlan] = Field(default_factory=list, description="Available room plans")


class Favorite(BaseModel):
    """Favorite hotel model."""
    hotel_id: str
    hotel_data: dict
    created_at: datetime


class SearchHistory(BaseModel):
    """Search history model."""
    id: Optional[int] = None
    query: str
    place: str
    place_type: Optional[str] = None
    created_at: datetime


class ApiResponse(BaseModel):
    """Generic API response model."""
    success: bool = True
    message: str = ""
    data: Optional[dict] = None
    error: Optional[str] = None


# ==================== Booking Models ====================

class SearchRequestTuniu(BaseModel):
    """Tuniu hotel search request model."""
    provider: str = Field("tuniu", description="Provider name")
    city_name: str = Field(..., description="City name (e.g., 北京, 上海)")
    check_in: str = Field(..., description="Check-in date YYYY-MM-DD")
    check_out: str = Field(..., description="Check-out date YYYY-MM-DD")
    adult_count: int = Field(2, ge=1, le=10, description="Number of adults")
    child_count: int = Field(0, ge=0, le=10, description="Number of children")
    keyword: Optional[str] = Field(None, description="Hotel name or brand keyword")
    page_num: int = Field(1, ge=1, description="Page number")
    query_id: Optional[str] = Field(None, description="Query ID for pagination")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "tuniu",
                "city_name": "北京",
                "check_in": "2026-04-01",
                "check_out": "2026-04-03",
                "adult_count": 2,
                "child_count": 0,
                "keyword": "希尔顿",
                "page_num": 1
            }
        }


class GuestInfo(BaseModel):
    """Guest information for booking."""
    first_name: str = Field(..., description="Guest first name (given name)")
    last_name: str = Field(..., description="Guest last name (family name)")


class RoomGuest(BaseModel):
    """Guest information for a single room."""
    guests: List[GuestInfo] = Field(..., description="List of guests in this room")


class BookingRequest(BaseModel):
    """Hotel booking request model."""
    provider: str = Field("tuniu", description="Provider name (only tuniu supports booking)")
    hotel_id: str = Field(..., description="Hotel ID")
    room_id: str = Field(..., description="Room type ID")
    pre_book_param: str = Field(..., description="Pre-booking parameter from hotel detail")
    check_in_date: str = Field(..., description="Check-in date YYYY-MM-DD")
    check_out_date: str = Field(..., description="Check-out date YYYY-MM-DD")
    room_count: int = Field(1, ge=1, le=10, description="Number of rooms")
    room_guests: List[RoomGuest] = Field(..., description="Guest info for each room")
    contact_name: str = Field(..., description="Contact person name")
    contact_phone: str = Field(..., description="Contact person phone")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "tuniu",
                "hotel_id": "123456",
                "room_id": "room_001",
                "pre_book_param": "abc123xyz",
                "check_in_date": "2026-04-01",
                "check_out_date": "2026-04-03",
                "room_count": 1,
                "room_guests": [
                    {
                        "guests": [
                            {"first_name": "三", "last_name": "张"}
                        ]
                    }
                ],
                "contact_name": "张三",
                "contact_phone": "13800138000"
            }
        }


class BookingResponse(BaseModel):
    """Hotel booking response model."""
    success: bool = Field(..., description="Whether booking was successful")
    order_id: Optional[str] = Field(None, description="Order ID")
    confirmation_number: Optional[str] = Field(None, description="Confirmation number")
    payment_url: Optional[str] = Field(None, description="Payment URL")
    error: Optional[str] = Field(None, description="Error message if failed")


class HotelTuniu(BaseModel):
    """Tuniu hotel summary model for search results."""
    hotel_id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    address: Optional[str] = Field(None, description="Hotel address")
    star_rating: Optional[float] = Field(None, description="Star rating")
    rating: Optional[float] = Field(None, description="User rating")
    price_per_night: Optional[float] = Field(None, description="Price per night")
    currency: Optional[str] = Field(None, description="Currency code")
    image_url: Optional[str] = Field(None, description="Main image URL")
    provider: str = Field("tuniu", description="Provider name")
    brand_name: Optional[str] = Field(None, description="Brand name")
    business: Optional[str] = Field(None, description="Business district")
    comment_digest: Optional[str] = Field(None, description="Comment digest")


class RoomPlanTuniu(BaseModel):
    """Tuniu room plan model for hotel detail."""
    room_id: str = Field(..., description="Room type ID")
    name: str = Field(..., description="Room name")
    description: Optional[str] = Field(None, description="Room description")
    price: Optional[float] = Field(None, description="Price per night")
    currency: Optional[str] = Field(None, description="Currency code")
    available: bool = Field(True, description="Whether room is available")
    amenities: List[str] = Field(default_factory=list, description="Room amenities")
    pre_book_param: Optional[str] = Field(None, description="Pre-booking parameter")
    room_count: int = Field(1, description="Available room count")


class HotelDetailTuniu(BaseModel):
    """Tuniu detailed hotel model."""
    hotel_id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    address: Optional[str] = Field(None, description="Hotel address")
    star_rating: Optional[float] = Field(None, description="Star rating")
    rating: Optional[float] = Field(None, description="User rating")
    price_per_night: Optional[float] = Field(None, description="Starting price per night")
    currency: Optional[str] = Field(None, description="Currency code")
    image_url: Optional[str] = Field(None, description="Main image URL")
    images: List[str] = Field(default_factory=list, description="Gallery images")
    description: Optional[str] = Field(None, description="Hotel description")
    amenities: List[str] = Field(default_factory=list, description="Hotel amenities")
    room_plans: List[RoomPlanTuniu] = Field(default_factory=list, description="Available room plans")
    provider: str = Field("tuniu", description="Provider name")
    supports_booking: bool = Field(True, description="Whether booking is supported")
    pre_book_param: Optional[str] = Field(None, description="Pre-booking parameter")


class ProviderInfo(BaseModel):
    """Provider information model."""
    id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Provider display name")
    description: str = Field(..., description="Provider description")
    supports_booking: bool = Field(..., description="Whether booking is supported")
    supports_pagination: bool = Field(..., description="Whether pagination is supported")
