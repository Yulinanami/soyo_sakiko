"""
Redis Cache Service
"""

import json
from typing import Optional, Any
from datetime import timedelta
import redis.asyncio as redis
from app.config import settings


class CacheService:
    """Redis cache service for caching API responses"""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        await self.connect()
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl_seconds: int = 300  # 5 minutes default
    ):
        """Set cached value with TTL"""
        await self.connect()
        try:
            await self._redis.setex(
                key, timedelta(seconds=ttl_seconds), json.dumps(value, default=str)
            )
        except Exception as e:
            print(f"Cache set error: {e}")

    async def delete(self, key: str):
        """Delete cached value"""
        await self.connect()
        try:
            await self._redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")

    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        await self.connect()
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            print(f"Cache clear pattern error: {e}")

    @staticmethod
    def make_key(*parts) -> str:
        """Create cache key from parts"""
        return ":".join(str(p) for p in parts)


# Global cache instance
cache = CacheService()


# Cache key patterns
class CacheKeys:
    @staticmethod
    def novel_search(sources: list, tags: list, page: int, sort_by: str) -> str:
        sources_str = ",".join(sorted(sources))
        tags_str = ",".join(sorted(tags))
        return cache.make_key("novels", "search", sources_str, tags_str, page, sort_by)

    @staticmethod
    def novel_detail(source: str, novel_id: str) -> str:
        return cache.make_key("novels", "detail", source, novel_id)

    @staticmethod
    def novel_chapters(source: str, novel_id: str) -> str:
        return cache.make_key("novels", "chapters", source, novel_id)

    @staticmethod
    def chapter_content(source: str, novel_id: str, chapter: int) -> str:
        return cache.make_key("novels", "content", source, novel_id, chapter)
