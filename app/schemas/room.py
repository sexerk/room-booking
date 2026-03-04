from pydantic import BaseModel, Field, ConfigDict
from app.schemas.amenity import Amenity


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    floor: int = Field(..., ge=1, le=100)
    capacity: int = Field(..., ge=1, le=1000)
    price_per_hour: float = Field(..., gt=0)
    is_active: bool = True


class RoomCreate(RoomBase):
    amenity_ids: list[int] | None = []


class RoomUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    floor: int | None = Field(None, ge=1, le=100)
    capacity: int | None = Field(None, ge=1, le=1000)
    price_per_hour: float | None = Field(None, gt=0)
    is_active: bool | None = None
    amenity_ids: list[int] | None = None


class Room(RoomBase):
    id: int
    amenities: list[Amenity] = []

    model_config = ConfigDict(from_attributes=True)


class RoomAvailability(Room):
    available: bool = True