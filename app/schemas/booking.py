from pydantic import BaseModel, ConfigDict, validator
from typing import Optional
from datetime import datetime
from app.models.booking import BookingStatus
from app.schemas.user import UserResponse
from app.schemas.room import Room


class BookingBase(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None


class BookingCreate(BookingBase):

    @validator('end_time')
    def validate_dates(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    purpose: Optional[str] = None
    status: Optional[BookingStatus] = None


class Booking(BookingBase):
    id: int
    user_id: int
    status: BookingStatus
    total_price: float
    created_at: datetime
    updated_at: Optional[datetime]

    user: Optional[UserResponse] = None
    room: Optional[Room] = None

    model_config = ConfigDict(from_attributes=True)


class BookingConfirm(BaseModel):
    confirm: bool = True