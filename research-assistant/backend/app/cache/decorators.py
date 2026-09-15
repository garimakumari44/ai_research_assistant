"""
Caching decorators.

Provides decorators for automatically caching the results
of asynchronous function calls.
"""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Awaitable, Callable

from app.cache.service import cache

AsyncFunction = Callable[..., Awaitable[Any]]


def _default_key_builder(
    func_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """
    Build a deterministic cache key based on the
    function name and arguments.
    """

    payload = {
        "args": args,
        "kwargs": kwargs,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        default=str,
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()

    return f"{func_name}:{digest}"


def cache_result(
    ttl: int = 3600,
    key_builder: Callable[
        [str, tuple[Any, ...], dict[str, Any]],
        str,
    ]
    | None = None,
) -> Callable[[AsyncFunction], AsyncFunction]:
    """
    Cache the result of an async function.

    Args:
        ttl:
            Cache expiration in seconds.

        key_builder:
            Optional custom cache-key generator.

    Example:

        @cache_result(ttl=600)

        async def expensive():
            ...
    """

    def decorator(
        func: AsyncFunction,
    ) -> AsyncFunction:

        @functools.wraps(func)
        async def wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> Any:

            builder = (
                key_builder
                or _default_key_builder
            )

            key = builder(
                func.__name__,
                args,
                kwargs,
            )

            cached = await cache.get(key)

            if cached is not None:
                return cached

            result = await func(
                *args,
                **kwargs,
            )

            await cache.set(
                key,
                result,
                expire=ttl,
            )

            return result

        return wrapper

    return decorator


def invalidate_cache(
    key_builder: Callable[
        [str, tuple[Any, ...], dict[str, Any]],
        str,
    ]
):
    """
    Delete a cache entry after a function executes.

    Useful after updates/deletes.
    """

    def decorator(func):

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            result = await func(
                *args,
                **kwargs,
            )

            key = key_builder(
                func.__name__,
                args,
                kwargs,
            )

            await cache.delete(key)

            return result

        return wrapper

    return decorator