import hashlib
import json
from typing import List, Any
from app.cache.redis_client import redis_client


class RoomCache:

    ROOM_PREFIX = "room:"
    ROOM_LIST_PREFIX = "rooms:list:"
    ROOM_AVAILABILITY_PREFIX = "room:avail:"

    ROOM_TTL = 300  # 5 минут
    ROOM_LIST_TTL = 300  # 5 минут
    AVAILABILITY_TTL = 60  # 1 минута

    def __init__(self):
        self.client = redis_client

    def _get_room_key(self, room_id: int) -> str:
        return f"{self.ROOM_PREFIX}{room_id}"

    def _get_list_key(self, skip: int, limit: int, **filters) -> str:
        filter_str = json.dumps(filters, sort_keys=True)
        hash_str = hashlib.md5(filter_str.encode()).hexdigest()[:8]
        return f"{self.ROOM_LIST_PREFIX}{skip}:{limit}:{hash_str}"

    async def get(self, room_id: int) -> Any | None:
        key = self._get_room_key(room_id)
        return await self.client.get_json(key)

    async def set(self, room_id: int, room_data: Any) -> bool:
        key = self._get_room_key(room_id)
        return await self.client.set(key, room_data, expire=self.ROOM_TTL)

    async def get_list(self, skip: int, limit: int, **filters) -> list | None:
        key = self._get_list_key(skip, limit, **filters)
        return await self.client.get_json(key)

    async def set_list(self, skip: int, limit: int, rooms: List, **filters) -> bool:
        key = self._get_list_key(skip, limit, **filters)
        return await self.client.set(key, rooms, expire=self.ROOM_LIST_TTL)

    async def invalidate(self, room_id: int):
        key = self._get_room_key(room_id)
        await self.client.delete(key)

    async def invalidate_all(self):
        await self.client.clear_pattern(f"{self.ROOM_LIST_PREFIX}*")

    async def invalidate_room_availability(self, room_id: int):
        pattern = f"{self.ROOM_AVAILABILITY_PREFIX}{room_id}:*"
        await self.client.clear_pattern(pattern)