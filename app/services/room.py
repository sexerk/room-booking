from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.room import RoomRepository
from app.repositories.booking import BookingRepository
from app.schemas.room import RoomCreate, RoomUpdate
from app.models.room import Room
from app.core.exceptions import RoomNotFoundError
from app.cache.room_cache import RoomCache
from app.cache.availability_cache import AvailabilityCache
from datetime import datetime


class RoomService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.room_repo = RoomRepository(db)
        self.booking_repo = BookingRepository(db)
        self.room_cache = RoomCache()
        self.availability_cache = AvailabilityCache()

    async def create_room(self, room_data: RoomCreate) -> Room:
        room = await self.room_repo.create(
            name=room_data.name,
            description=room_data.description,
            floor=room_data.floor,
            capacity=room_data.capacity,
            price_per_hour=room_data.price_per_hour,
            is_active=room_data.is_active
        )

        if room_data.amenity_ids:
            await self.room_repo.add_amenities(room.id, room_data.amenity_ids)

        await self.room_cache.invalidate_all()

        return room

    async def get_room(self, room_id: int) -> Room:
        cached = await self.room_cache.get(room_id)
        if cached:
            return cached

        room = await self.room_repo.get_with_amenities(room_id)
        if not room:
            raise RoomNotFoundError()

        await self.room_cache.set(room_id, room)

        return room

    async def get_rooms(
            self,
            skip: int = 0,
            limit: int = 100,
            min_capacity: int | None = None,
            floor: int | None = None,
            amenity_ids: list[int] | None = None,
            use_cache: bool = True
    ) -> list[Room]:
        if use_cache and not any([min_capacity, floor, amenity_ids]):
            cached = await self.room_cache.get_list(skip, limit)
            if cached is not None:
                return cached

        rooms = await self.room_repo.get_active_rooms(
            skip=skip,
            limit=limit,
            min_capacity=min_capacity,
            floor=floor,
            amenity_ids=amenity_ids
        )

        if use_cache and not any([min_capacity, floor, amenity_ids]):
            await self.room_cache.set_list(skip, limit, rooms)

        return rooms

    async def update_room(self, room_id: int, room_data: RoomUpdate) -> Room:
        room = await self.room_repo.get(room_id)
        if not room:
            raise RoomNotFoundError()

        update_data = room_data.model_dump(exclude_unset=True, exclude={'amenity_ids'})
        if update_data:
            room = await self.room_repo.update(room_id, **update_data)

        if room_data.amenity_ids is not None:
            current_amenities = {a.id for a in room.amenities}
            new_amenities = set(room_data.amenity_ids)

            to_add = new_amenities - current_amenities
            if to_add:
                await self.room_repo.add_amenities(room_id, list(to_add))

            to_remove = current_amenities - new_amenities
            if to_remove:
                await self.room_repo.remove_amenities(room_id, list(to_remove))

        await self.room_cache.invalidate(room_id)
        await self.room_cache.invalidate_all()
        await self.availability_cache.invalidate_room(room_id)

        return await self.get_room(room_id)

    async def delete_room(self, room_id: int, hard_delete: bool = False) -> bool:
        room = await self.room_repo.get(room_id)
        if not room:
            raise RoomNotFoundError()

        if hard_delete:
            future_bookings = await self.booking_repo.get_room_bookings(
                room_id=room_id,
                start_time=datetime.utcnow()
            )
            if future_bookings:
                raise ValueError("Cannot delete room with future bookings")

            result = await self.room_repo.delete(room_id)
        else:
            result = await self.room_repo.update(room_id, is_active=False)
            result = bool(result)

        if result:
            await self.room_cache.invalidate(room_id)
            await self.room_cache.invalidate_all()
            await self.availability_cache.invalidate_room(room_id)

        return result

    async def get_available_rooms(
            self,
            start_time: datetime,
            end_time: datetime,
            min_capacity: int | None = None,
            floor: int | None = None,
            amenity_ids: list[int] | None = None
    ) -> list[Room]:
        rooms = await self.get_rooms(
            skip=0,
            limit=1000,
            min_capacity=min_capacity,
            floor=floor,
            amenity_ids=amenity_ids,
            use_cache=False
        )

        available_rooms = []
        for room in rooms:
            from app.services.booking import BookingService
            booking_service = BookingService(self.db)

            is_available = await booking_service.check_availability(
                room_id=room.id,
                start_time=start_time,
                end_time=end_time
            )

            if is_available:
                available_rooms.append(room)

        return available_rooms


async def get_room_service(db: AsyncSession = None) -> RoomService:
    return RoomService(db)