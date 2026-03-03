import json
from typing import Optional, Any
from redis.asyncio import Redis
from app.core.config import settings


class RedisClient:

    def __init__(self):
        self.client: Optional[Redis] = None

    async def init(self):
        self.client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def get(self, key: str, default: Any = None) -> Any:
        if not self.client:
            await self.init()
        value = await self.client.get(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except Exception:
            return value

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        if not self.client:
            await self.init()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        return await self.client.set(key, value, ex=expire)

    async def delete(self, *keys: str) -> int:
        if not self.client:
            await self.init()
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        if not self.client:
            await self.init()
        return await self.client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        if not self.client:
            await self.init()
        return await self.client.expire(key, seconds)

    async def clear_pattern(self, pattern: str) -> int:
        if not self.client:
            await self.init()
        keys = await self.client.keys(pattern)
        if keys:
            return await self.client.delete(*keys)
        return 0

    async def incr(self, key: str) -> int:
        if not self.client:
            await self.init()
        return await self.client.incr(key)

    async def get_json(self, key: str, default: Any = None) -> Any:
        value = await self.get(key)
        if value is None:
            return default
        return value


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    await redis_client.init()
    return redis_client
