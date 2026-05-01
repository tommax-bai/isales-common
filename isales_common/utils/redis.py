"""Async Redis client factory.

Each service builds its own client at startup (no module-level singleton — keeps
connection lifecycle explicit and per-process testable).
"""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis, from_url


def get_redis(url: str, *, decode_responses: bool = True) -> Redis[Any]:
    """Build an async Redis client from a URL like ``redis://localhost:6379/0``.

    `decode_responses=True` returns ``str`` from string commands; binary use cases
    (e.g. raw audio buffers) MUST pass ``decode_responses=False``.
    """
    return from_url(url, decode_responses=decode_responses)
