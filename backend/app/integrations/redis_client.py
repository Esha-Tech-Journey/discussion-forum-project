import redis.asyncio as redis
import json

from app.core.config import settings


class RedisClient:
    """
    Handles Redis connection & pub/sub.
    """

    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            retry_on_timeout=False,
        )

    # ==============================
    # Publish Event
    # ==============================
    async def publish(
        self,
        channel: str,
        message: dict
    ):
        await self.redis.publish(
            channel,
            json.dumps(message)
        )

    # ==============================
    # Subscribe Channel
    # ==============================
    async def subscribe(self, channel: str):

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)

        return pubsub


redis_client = RedisClient()
