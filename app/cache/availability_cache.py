import hashlib
from datetime import datetime
from typing import Optional
from app.cache.redis_client import redis_client


class AvailabilityCache:

    PREFIX = "availability:"
    TTL = 60  # 1 минута

    def __init__(self):
        self.client = redis_client

    def _get_key(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> str:
        start_str = start_time.strftime("%Y%m%d%H%M")
        end_str = end_time.strftime("%Y%m%d%H%M")

        base = f"{room_id}:{start_str}:{end_str}"
        hash_str = hashlib.md5(base.encode()).hexdigest()[:16]

        return f"{self.PREFIX}{hash_str}"

    async def get_availability(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> Optional[bool]:

        key = self._get_key(room_id, start_time, end_time)
        value = await self.client.get(key)

        if value is not None:
            return value == "1"
        return None

    async def set_availability(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime,
            is_available: bool
    ) -> bool:

        key = self._get_key(room_id, start_time, end_time)
        value = "1" if is_available else "0"

        return await self.client.set(key, value, expire=self.TTL)

    async def invalidate_room(self, room_id: int):

        pattern = f"{self.PREFIX}*{room_id}*"
        await self.client.clear_pattern(pattern)

    async def invalidate_room_interval(
            self,
            room_id: int,
            start_time: datetime,
            end_time: datetime
    ):

        await self.invalidate_room(room_id)