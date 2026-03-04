from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Text, Index, Float
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.schemas.booking import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    purpose = Column(Text)
    total_price = Column(Float, nullable=False)

    user = relationship("User", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")

    __table_args__ = (
        Index("ix_bookings_room_time", "room_id", "start_time", "end_time"),
        Index("ix_bookings_user_time", "user_id", "start_time", "end_time"),
        Index("ix_bookings_status", "status"),
    )

    def __repr__(self):
        return f"<Booking {self.id}: Room {self.room_id} by User {self.user_id}>"