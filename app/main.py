from fastapi import FastAPI
from app.api.endpoints import auth, rooms, bookings, admin

app = FastAPI(title="Room Booking API")

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(rooms.router, prefix="/api/v1/rooms")
app.include_router(bookings.router, prefix="/api/v1/bookings")
app.include_router(admin.router, prefix="/api/v1/admin")
