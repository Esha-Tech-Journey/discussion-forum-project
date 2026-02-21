import time
import asyncio
import logging

from fastapi import HTTPException, status

from app.integrations.redis_client import (
    redis_client
)


class RateLimiter:
    """
    Redis-based rate limiter.
    """

    def __init__(
        self,
        key_prefix: str,
        limit: int,
        window_seconds: int,
    ):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window_seconds
        self.logger = logging.getLogger(__name__)

    # ==============================
    # Check limit
    # ==============================
    async def check_limit(
        self,
        identifier: str
    ):

        key = f"{self.key_prefix}:{identifier}"

        try:
            current_count = await asyncio.wait_for(
                redis_client.redis.get(key),
                timeout=1.0,
            )

            if current_count and int(current_count) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            pipe = redis_client.redis.pipeline()

            pipe.incr(key, 1)
            pipe.expire(key, self.window)

            await asyncio.wait_for(
                pipe.execute(),
                timeout=1.0,
            )
        except HTTPException:
            raise
        except Exception:
            # Fail-open on limiter backend issues so auth/comments don't hang.
            self.logger.warning(
                "Rate limiter backend unavailable; allowing request for %s",
                identifier,
            )
            return
