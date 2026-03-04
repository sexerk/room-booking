from pydantic import BaseModel, ConfigDict, validator
from datetime import datetime
from app.schemas.user import UserResponse
from app.schemas.room import Room
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    COMPLETED = "completed"


class BookingBase(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime
    purpose: str | None = None


class BookingCreate(BookingBase):

    @validator('end_time')
    def validate_dates(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class BookingUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    purpose: str | None = None
    status: BookingStatus | None = None


class Booking(BookingBase):
    id: int
    user_id: int
    status: BookingStatus
    total_price: float
    created_at: datetime
    updated_at: datetime | None

    user: UserResponse | None = None
    room: Room | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingConfirm(BaseModel):
    confirm: bool = True