from fastapi import FastAPI
from app.api.endpoints import auth, rooms, bookings, admin
from sqlalchemy import text
from app.db.session import async_session_maker
import redis.asyncio as redis
import traceback

app = FastAPI(title="Room Booking API")

@app.get("/health")
async def health_check():
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
        print("=== DB Error ===")
        print(traceback.format_exc())

    try:
        r = redis.Redis(host="redis", port=6379, db=0)
        await r.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {e}"
        print("=== Redis Error ===")
        print(traceback.format_exc())

    return {
        "status": "ok",
        "database": db_status,
        "redis": redis_status,
    }

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(rooms.router, prefix="/api/v1/rooms")
app.include_router(bookings.router, prefix="/api/v1/bookings")
app.include_router(admin.router, prefix="/api/v1/admin")

@app.get("/")
async def root():
    return {"status": "ok"}