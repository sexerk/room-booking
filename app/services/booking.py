from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.booking import BookingRepository
from app.repositories.room import RoomRepository
from app.repositories.user import UserRepository
from app.schemas.booking import BookingCreate
from app.models.booking import Booking, BookingStatus
from app.core.exceptions import (
    BookingConflictError,
    RoomNotFoundError,
    UserNotFoundError,
    InvalidBookingDatesError,
    BookingNotFoundError,
    BookingCancellationError,
    PermissionDeniedError
)
from app.core.config import settings
from app.cache.availability_cache import AvailabilityCache


class BookingService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.room_repo = RoomRepository(db)
        self.user_repo = UserRepository(db)
        self.cache = AvailabilityCache()

    async def create_booking(
            self,
            user_id: int,
            booking_data: BookingCreate
    ) -> Booking:

        user = await self.user_repo.get(user_id)
        if not user:
            raise UserNotFoundError()

        if not user.is_active:
            raise PermissionDeniedError("User account is inactive")

        room = await self.room_repo.get(booking_data.room_id)
        if not room:
            raise RoomNotFoundError()

        if not room.is_active:
            raise RoomNotFoundError("Room is not available for booking")

        await self._validate_booking_dates(
            booking_data.start_time,
            booking_data.end_time
        )

        await self._check_availability(
            room_id=booking_data.room_id,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time
        )

        total_price = self._calculate_price(
            room.price_per_hour,
            booking_data.start_time,
            booking_data.end_time
        )

        booking = await self.booking_repo.create(
            user_id=user_id,
            room_id=booking_data.room_id,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            purpose=booking_data.purpose,
            total_price=total_price,
            status=BookingStatus.PENDING
        )

        from app.tasks.booking_tasks import expire_pending_booking, send_booking_reminder
        expire_pending_booking.apply_async(
            args=[booking.id],
            countdown=settings.PENDING_EXPIRY_MINUTES * 60
        )

        remind_before = settings.REMINDER_MINUTES_BEFORE * 60
        time_until_start = (booking.start_time - datetime.now(timezone.utc)).total_seconds()
        if time_until_start > remind_before:
            send_booking_reminder.apply_async(
                args=[booking.id],
                countdown=time_until_start - remind_before
            )

        await self.cache.invalidate_room(booking_data.room_id)

        return booking

    async def confirm_booking(
            self,
            booking_id: int,
            user_id: int,
            is_admin: bool = False
    ) -> Booking:

        booking = await self.booking_repo.get_with_relations(booking_id)
        if not booking:
            raise BookingNotFoundError()

        if booking.user_id != user_id and not is_admin:
            raise PermissionDeniedError("You can only confirm your own bookings")

        if booking.status != BookingStatus.PENDING:
            raise InvalidBookingDatesError(
                f"Cannot confirm booking with status {booking.status}"
            )

        if booking.created_at + timedelta(minutes=settings.PENDING_EXPIRY_MINUTES) < datetime.now(timezone.utc):
            booking.status = BookingStatus.EXPIRED
            await self.db.commit()
            raise BookingCancellationError("Booking has expired")

        booking.status = BookingStatus.CONFIRMED
        await self.db.commit()
        await self.db.refresh(booking)

        await self.cache.invalidate_room(booking.room_id)

        return booking

    async def cancel_booking(
            self,
            booking_id: int,
            user_id: int,
            is_admin: bool = False
    ) -> Booking:

        booking = await self.booking_repo.get_with_relations(booking_id)
        if not booking:
            raise BookingNotFoundError()

        if booking.user_id != user_id and not is_admin:
            raise PermissionDeniedError("You can only cancel your own bookings")

        if booking.status == BookingStatus.CANCELLED:
            raise BookingCancellationError("Booking is already cancelled")

        if booking.status == BookingStatus.COMPLETED:
            raise BookingCancellationError("Cannot cancel completed booking")

        if booking.start_time < datetime.now(timezone.utc):
            raise BookingCancellationError("Cannot cancel booking that has already started")

        booking.status = BookingStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(booking)

        await self.cache.invalidate_room(booking.room_id)

        return booking

    async def get_user_bookings(
            self,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        return await self.booking_repo.get_user_bookings(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status
        )

    async def get_booking(
            self,
            booking_id: int,
            user_id: Optional[int] = None,
            is_admin: bool = False
    ) -> Booking:
        booking = await self.booking_repo.get_with_relations(booking_id)
        if not booking:
            raise BookingNotFoundError()

        if user_id and booking.user_id != user_id and not is_admin:
            raise PermissionDeniedError("You can only view your own bookings")

        return booking

    async def get_room_bookings(
            self,
            room_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Booking]:
        return await self.booking_repo.get_room_bookings(
            room_id=room_id,
            start_time=start_date,
            end_time=end_date
        )

    async def check_availability(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> bool:
        cached = await self.cache.get_availability(
            room_id, start_time, end_time
        )
        if cached is not None:
            return cached

        conflicting = await self.booking_repo.check_conflict(
            room_id=room_id,
            start_time=start_time,
            end_time=end_time
        )

        is_available = conflicting is None

        await self.cache.set_availability(
            room_id, start_time, end_time, is_available
        )

        return is_available

    async def _check_availability(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime,
            exclude_booking_id: Optional[int] = None
    ):
        conflicting = await self.booking_repo.check_conflict(
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            exclude_booking_id=exclude_booking_id
        )

        if conflicting:
            raise BookingConflictError(
                f"Room is already booked from {conflicting.start_time} to {conflicting.end_time}"
            )

    async def _validate_booking_dates(self, start_time: datetime, end_time: datetime):
        now = datetime.now(timezone.utc)

        if start_time >= end_time:
            raise InvalidBookingDatesError("Start time must be before end time")

        if start_time < now:
            raise InvalidBookingDatesError("Cannot book in the past")

        min_duration = timedelta(minutes=settings.MIN_BOOKING_MINUTES)
        if end_time - start_time < min_duration:
            raise InvalidBookingDatesError(
                f"Booking duration must be at least {settings.MIN_BOOKING_MINUTES} minutes"
            )

        max_duration = timedelta(days=settings.MAX_BOOKING_DAYS)
        if end_time - start_time > max_duration:
            raise InvalidBookingDatesError(
                f"Booking duration cannot exceed {settings.MAX_BOOKING_DAYS} days"
            )

        max_future = now + timedelta(days=30)
        if start_time > max_future:
            raise InvalidBookingDatesError("Cannot book more than 30 days in advance")

    def _calculate_price(self, price_per_hour: float, start_time: datetime, end_time: datetime) -> float:
        hours = (end_time - start_time).total_seconds() / 3600
        return round(price_per_hour * hours, 2)

    async def expire_pending_bookings(self):

        expired = await self.booking_repo.get_expired_pending(
            minutes=settings.PENDING_EXPIRY_MINUTES
        )

        for booking in expired:
            booking.status = BookingStatus.EXPIRED
            await self.cache.invalidate_room(booking.room_id)

        if expired:
            await self.db.commit()

        return len(expired)


async def get_booking_service(db: AsyncSession = None) -> BookingService:
    return BookingService(db)