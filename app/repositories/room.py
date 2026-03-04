from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.room import Room
from app.models.amenity import room_amenity
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):

    def __init__(self, db: AsyncSession):
        super().__init__(Room, db)

    async def get_with_amenities(self, id: int) ->Room | None:
        result = await self.db.execute(
            select(Room)
            .options(selectinload(Room.amenities))
            .where(Room.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active_rooms(
            self,
            skip: int = 0,
            limit: int = 100,
            min_capacity: int | None = None,
            floor: int | None = None,
            amenity_ids: list[int] | None = None
    ) -> list[Room]:
        query = select(Room).options(selectinload(Room.amenities)).where(Room.is_active.is_(True))

        if min_capacity:
            query = query.where(Room.capacity >= min_capacity)

        if floor:
            query = query.where(Room.floor == floor)

        if amenity_ids:
            subquery = (
                select(room_amenity.c.room_id)
                .where(room_amenity.c.amenity_id.in_(amenity_ids))
                .group_by(room_amenity.c.room_id)
                .having(func.count() == len(amenity_ids))
            )
            query = query.where(Room.id.in_(subquery))

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_amenities(self, room_id: int, amenity_ids: list[int]):
        room = await self.get(room_id)
        if not room:
            return False

        for amenity_id in amenity_ids:
            await self.db.execute(
                room_amenity.insert().values(
                    room_id=room_id,
                    amenity_id=amenity_id
                )
            )

        await self.db.commit()
        return True

    async def remove_amenities(self, room_id: int, amenity_ids: list[int]):
        for amenity_id in amenity_ids:
            await self.db.execute(
                room_amenity.delete().where(
                    and_(
                        room_amenity.c.room_id == room_id,
                        room_amenity.c.amenity_id == amenity_id
                    )
                )
            )

        await self.db.commit()
        return True