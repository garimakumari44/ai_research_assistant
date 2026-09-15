"""
Redis cache service.

Provides a high-level interface for interacting with Redis.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class CacheService:
    """
    High-level asynchronous Redis service.
    """

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    # ==========================================================
    # Connection Management
    # ==========================================================

    async def connect(self) -> None:
        """
        Initialize the Redis connection.
        """

        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

            await self._client.ping()

    async def disconnect(self) -> None:
        """
        Close Redis connection.
        """

        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """
        Return the active Redis client.
        """

        if self._client is None:
            raise RuntimeError(
                "Redis is not connected."
            )

        return self._client

    # ==========================================================
    # Basic Operations
    # ==========================================================

    async def get(
        self,
        key: str,
    ) -> Any | None:
        """
        Retrieve a cached value.
        """

        value = await self.client.get(key)

        if value is None:
            return None

        try:
            return json.loads(value)
        except Exception:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        """
        Store a value.
        """

        if not isinstance(value, str):
            value = json.dumps(value)

        return await self.client.set(
            key,
            value,
            ex=expire,
        )

    async def delete(
        self,
        key: str,
    ) -> bool:
        """
        Delete a cache key.
        """

        deleted = await self.client.delete(key)

        return deleted > 0

    async def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check if a key exists.
        """

        return bool(
            await self.client.exists(key)
        )

    # ==========================================================
    # Expiration
    # ==========================================================

    async def expire(
        self,
        key: str,
        seconds: int,
    ) -> bool:
        """
        Set TTL on a key.
        """

        return await self.client.expire(
            key,
            seconds,
        )

    async def ttl(
        self,
        key: str,
    ) -> int:
        """
        Return remaining TTL.
        """

        return await self.client.ttl(key)

    # ==========================================================
    # Numeric Operations
    # ==========================================================

    async def increment(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """
        Increment integer value.
        """

        return await self.client.incr(
            key,
            amount,
        )

    async def decrement(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """
        Decrement integer value.
        """

        return await self.client.decr(
            key,
            amount,
        )

    # ==========================================================
    # Bulk Operations
    # ==========================================================

    async def delete_pattern(
        self,
        pattern: str,
    ) -> int:
        """
        Delete all keys matching a pattern.
        """

        keys = []

        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)

        if not keys:
            return 0

        return await self.client.delete(*keys)

    async def clear(self) -> None:
        """
        Clear the current Redis database.
        """

        await self.client.flushdb()

    # ==========================================================
    # Health
    # ==========================================================

    async def ping(self) -> bool:
        """
        Check Redis availability.
        """

        try:
            return await self.client.ping()
        except Exception:
            return False


# ==========================================================
# Singleton
# ==========================================================

cache = CacheService()