from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from app.schemas.amenity import Amenity


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    floor: int = Field(..., ge=1, le=100)
    capacity: int = Field(..., ge=1, le=1000)
    price_per_hour: float = Field(..., gt=0)
    is_active: bool = True


class RoomCreate(RoomBase):
    amenity_ids: Optional[List[int]] = []


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    floor: Optional[int] = Field(None, ge=1, le=100)
    capacity: Optional[int] = Field(None, ge=1, le=1000)
    price_per_hour: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    amenity_ids: Optional[List[int]] = None


class Room(RoomBase):
    id: int
    amenities: List[Amenity] = []

    model_config = ConfigDict(from_attributes=True)


class RoomAvailability(Room):
    available: bool = True