import asyncio
import logging
from datetime import datetime, timedelta, timezone
from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from app.tasks.worker import celery_app
from app.db.session import async_session_maker
from app.services.booking import BookingService
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseTask(Task):

    def after_return(self, *args, **kwargs):
        pass  # сессия закрывается внутри каждой задачи через async with


@celery_app.task(
    name="expire_pending_booking",
    base=DatabaseTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def expire_pending_booking(self, booking_id: int):
    logger.info(f"Checking pending booking {booking_id} for expiration")

    async def _expire():
        async with async_session_maker() as db:
            try:
                service = BookingService(db)
                booking = await service.booking_repo.get(booking_id)

                if not booking:
                    logger.warning(f"Booking {booking_id} not found")
                    return

                if booking.status != "pending":
                    logger.info(f"Booking {booking_id} already {booking.status}")
                    return

                expiry_time = booking.created_at
                if expiry_time.tzinfo is None:
                    expiry_time = expiry_time.replace(tzinfo=timezone.utc)

                if expiry_time + timedelta(minutes=settings.PENDING_EXPIRY_MINUTES) < datetime.now(timezone.utc):
                    booking.status = "expired"
                    await db.commit()
                    logger.info(f"Booking {booking_id} expired")

                    from app.cache.availability_cache import AvailabilityCache
                    cache = AvailabilityCache()
                    await cache.invalidate_room(booking.room_id)

            except Exception as e:
                logger.error(f"Error expiring booking {booking_id}: {e}")
                raise self.retry(exc=e)

    asyncio.run(_expire())


@celery_app.task(
    name="send_booking_reminder",
    base=DatabaseTask,
    bind=True
)
def send_booking_reminder(self, booking_id: int):
    logger.info(f"Sending reminder for booking {booking_id}")

    async def _remind():
        async with async_session_maker() as db:
            try:
                service = BookingService(db)
                booking = await service.booking_repo.get_with_relations(booking_id)

                if not booking:
                    logger.warning(f"Booking {booking_id} not found")
                    return

                if booking.status != "confirmed":
                    logger.info(f"Booking {booking_id} is {booking.status}, skipping reminder")
                    return

                logger.info(
                    f"REMINDER: Booking {booking_id} for {booking.user.email} "
                    f"in room {booking.room.name} at {booking.start_time}"
                )

            except Exception as e:
                logger.error(f"Error sending reminder for booking {booking_id}: {e}")

    asyncio.run(_remind())


@celery_app.task(name="expire_pending_bookings")
def expire_pending_bookings():
    logger.info("Running periodic task: expire_pending_bookings")

    async def _run():
        async with async_session_maker() as db:
            service = BookingService(db)
            count = await service.expire_pending_bookings()
            logger.info(f"Expired {count} pending bookings")

    asyncio.run(_run())


@celery_app.task(name="clean_expired_cache")
def clean_expired_cache():
    logger.info("Cleaning expired cache")