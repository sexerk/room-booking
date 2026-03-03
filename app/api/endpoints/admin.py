from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.session import get_db
from app.schemas.booking import Booking
from app.schemas.user import UserResponse
from app.services.booking import get_booking_service
from app.models.user import User
from app.models.booking import BookingStatus
from app.api.deps import get_current_admin_user

router = APIRouter(
    # prefix="/admin",
    tags=["admin"]
)


@router.get("/bookings", response_model=List[Booking])
async def get_all_bookings(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        user_id: Optional[int] = Query(None),
        room_id: Optional[int] = Query(None),
        status: Optional[BookingStatus] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):

    booking_service = await get_booking_service(db)
    bookings = await booking_service.booking_repo.get_multi(
        skip=skip,
        limit=limit
    )
    return bookings


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        is_active: Optional[bool] = Query(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):

    from app.repositories.user import UserRepository
    repo = UserRepository(db)
    filters = {}
    if is_active is not None:
        filters['is_active'] = is_active

    users = await repo.get_multi(skip=skip, limit=limit, **filters)
    return users


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):

    from app.repositories.user import UserRepository
    repo = UserRepository(db)
    user = await repo.get(user_id)

    if not user:
        return {"error": "User not found"}

    user.is_active = not user.is_active
    await db.commit()

    return {"user_id": user_id, "is_active": user.is_active}


@router.get("/stats")
async def get_stats(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):

    from app.repositories.user import UserRepository
    from app.repositories.room import RoomRepository
    from app.repositories.booking import BookingRepository

    user_repo = UserRepository(db)
    room_repo = RoomRepository(db)
    booking_repo = BookingRepository(db)

    total_users = await user_repo.count()
    total_rooms = await room_repo.count(is_active=True)
    total_bookings = await booking_repo.count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_bookings = await booking_repo.count(start_time__gte=today_start)

    return {
        "total_users": total_users,
        "total_rooms": total_rooms,
        "total_bookings": total_bookings,
        "today_bookings": today_bookings
    }