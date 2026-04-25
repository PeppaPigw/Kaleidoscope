"""Redis cache service for storing temporary data."""

import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class CacheService:
    """Async Redis cache service."""

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            r = await self._get_redis()
            value = await r.get(f"cache:{key}")
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning("cache_get_failed", key=key, error=str(e)[:100])
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds."""
        try:
            r = await self._get_redis()
            # Add timestamp
            if isinstance(value, dict):
                value["updated_at"] = datetime.utcnow().isoformat()
            serialized = json.dumps(value)
            await r.setex(f"cache:{key}", ttl, serialized)
            return True
        except Exception as e:
            logger.warning("cache_set_failed", key=key, error=str(e)[:100])
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            r = await self._get_redis()
            await r.delete(f"cache:{key}")
            return True
        except Exception as e:
            logger.warning("cache_delete_failed", key=key, error=str(e)[:100])
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


def get_cache_service() -> CacheService:
    """Factory for dependency injection."""
    return CacheService()
