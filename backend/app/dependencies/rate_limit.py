from fastapi import Request

from app.utils.rate_limiter import RateLimiter


# ==============================
# Login limiter
# ==============================

async def login_rate_limiter(
    request: Request
):

    limiter = RateLimiter(
        key_prefix="login",
        limit=5,
        window_seconds=60,
    )

    ip = request.client.host

    await limiter.check_limit(ip)


# ==============================
# Comment limiter
# ==============================

async def comment_rate_limiter(
    request: Request
):

    limiter = RateLimiter(
        key_prefix="comment",
        limit=20,
        window_seconds=60,
    )

    ip = request.client.host

    await limiter.check_limit(ip)
