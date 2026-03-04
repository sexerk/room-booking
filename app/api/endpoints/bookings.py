from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.booking import Booking, BookingCreate, BookingUpdate, BookingConfirm
from app.services.booking import get_booking_service
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.booking import BookingStatus

router = APIRouter(
    # prefix="/bookings",
    tags=["bookings"])

@router.get("/", response_model=List[Booking])
async def get_my_bookings(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        status: Optional[BookingStatus] = Query(None, description="Фильтр по статусу"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    booking_service = await get_booking_service(db)
    bookings = await booking_service.get_user_bookings(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )
    return bookings


@router.post("/", response_model=Booking, status_code=status.HTTP_201_CREATED)
async def create_booking(
        booking_data: BookingCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    booking_service = await get_booking_service(db)
    booking = await booking_service.create_booking(
        user_id=current_user.id,
        booking_data=booking_data
    )
    return booking


@router.get("/{booking_id}", response_model=Booking)
async def get_booking(
        booking_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    booking_service = await get_booking_service(db)
    booking = await booking_service.get_booking(
        booking_id=booking_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    return booking


@router.post("/{booking_id}/confirm", response_model=Booking)
async def confirm_booking(
        booking_id: int,
        confirm_data: BookingConfirm = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    booking_service = await get_booking_service(db)
    booking = await booking_service.confirm_booking(
        booking_id=booking_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    return booking


@router.post("/{booking_id}/cancel", response_model=Booking)
async def cancel_booking(
        booking_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    booking_service = await get_booking_service(db)
    booking = await booking_service.cancel_booking(
        booking_id=booking_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    return booking


@router.patch("/{booking_id}", response_model=Booking)
async def update_booking(
        booking_id: int,
        booking_data: BookingUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):

    # TODO: реализовать обновление
    pass