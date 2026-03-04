from sqlalchemy import Column, Integer, String, Boolean, Text, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")
    amenities = relationship("Amenity", secondary="room_amenity", back_populates="rooms")

    def __repr__(self):
        return f"<Room {self.name}>"