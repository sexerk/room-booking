from sqlalchemy.orm import relationship
from sqlalchemy import Table, ForeignKey, Column, Integer, String
from app.db.base import Base

class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    icon = Column(String(50))

    rooms = relationship("Room", secondary="room_amenity", back_populates="amenities")

    def __repr__(self):
        return f"<Amenity {self.name}>"




room_amenity = Table(
    "room_amenity",
    Base.metadata,
    Column("room_id", Integer, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True),
    Column("amenity_id", Integer, ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True)
)