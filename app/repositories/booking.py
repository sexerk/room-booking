from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import Booking, BookingStatus
from app.models.room import Room
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):

    def __init__(self, db: AsyncSession):
        super().__init__(Booking, db)

    async def create(
            self,
            user_id: int,
            room_id: int,
            start_time: datetime,
            end_time: datetime,
            purpose: str | None,
            total_price: float,
            status: BookingStatus
    ) -> Booking:
        booking = Booking(
            user_id=user_id,
            room_id=room_id,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            total_price=total_price,
            status=status
        )
        self.db.add(booking)
        await self.db.commit()

        result = await self.db.execute(
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.room).selectinload(Room.amenities)
            )
            .where(Booking.id == booking.id)
        )
        return result.scalar_one()

    async def get_with_relations(self, id: int) -> Booking | None:
        result = await self.db.execute(
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.room).selectinload(Room.amenities)
            )
            .where(Booking.id == id)
        )
        return result.scalar_one_or_none()

    async def get_user_bookings(
            self,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            status: BookingStatus | None = None
    ) -> list[Booking]:
        query = select(Booking).where(Booking.user_id == user_id)

        if status:
            query = query.where(Booking.status == status)

        query = query.order_by(Booking.start_time.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_room_bookings(
            self,
            room_id: int,
            start_time: datetime | None = None,
            end_time: datetime | None = None
    ) -> list[Booking]:
        query = select(Booking).where(
            Booking.room_id == room_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        )

        if start_time:
            query = query.where(Booking.end_time > start_time)

        if end_time:
            query = query.where(Booking.start_time < end_time)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_conflict(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime,
            exclude_booking_id: int | None = None
    ) -> Booking | None:
        query = select(Booking).where(
            Booking.room_id == room_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )

        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_expired_pending(self, minutes: int = 15) -> list[Booking]:
        from datetime import timezone
        expire_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        result = await self.db.execute(
            select(Booking).where(
                Booking.status == BookingStatus.PENDING,
                Booking.created_at <= expire_time
            )
        )
        return result.scalars().all()