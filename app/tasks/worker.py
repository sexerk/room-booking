from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "room_booking",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.booking_tasks",
        "app.tasks.periodic"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=15 * 60,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

celery_app.conf.beat_schedule = {
    "expire-pending-bookings": {
        "task": "expire_pending_bookings",
        "schedule": 60.0,
    },
    "clean-expired-cache": {
        "task": "clean_expired_cache",
        "schedule": 3600.0,
    },
}

if __name__ == "__main__":
    celery_app.start()