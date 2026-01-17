"""
Redis Cache Service
"""

import json
import logging
from typing import Optional, Any
from datetime import timedelta
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service for caching API responses"""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis (fail gracefully if unavailable)"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL, encoding="utf-8", decode_responses=True
                )
                # Test connection
                await self._redis.ping()
            except Exception as e:
                logger.warning("Redis connection failed (cache disabled): %s", e)
                self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            await self.connect()
            if self._redis is None:
                return None
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning("Cache get error: %s", e)
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
            logger.warning("Cache set error: %s", e)

    @staticmethod
    def make_key(*parts) -> str:
        """Create cache key from parts"""
        return ":".join(str(p) for p in parts)


# Global cache instance
cache = CacheService()


# Cache key patterns
class CacheKeys:
    @staticmethod
    def novel_detail(source: str, novel_id: str) -> str:
        return cache.make_key("novels", "detail", source, novel_id)

    @staticmethod
    def novel_chapters(source: str, novel_id: str) -> str:
        return cache.make_key("novels", "chapters", source, novel_id)

    @staticmethod
    def chapter_content(source: str, novel_id: str, chapter: int) -> str:
        return cache.make_key("novels", "content", source, novel_id, chapter)
