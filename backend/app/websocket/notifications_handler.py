import logging

from app.core.constants import RedisChannels
from app.websocket.events import WSEvents
from app.websocket.manager import manager
from app.integrations.redis_client import redis_client

logger = logging.getLogger(__name__)

def build_notification_payload(notification) -> dict:
    return {
        "event": WSEvents.NEW_NOTIFICATION,
        "data": {
            "notification_id": notification.id,
            "user_id": notification.user_id,
            "actor_id": notification.actor_id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "entity_type": notification.entity_type,
            "entity_id": notification.entity_id,
            "is_read": notification.is_read,
            "created_at": str(notification.created_at),
        },
    }


async def dispatch_notification_event(notification) -> None:
    payload = build_notification_payload(notification)

    try:
        await redis_client.publish(
            RedisChannels.NOTIFICATIONS,
            payload,
        )
        return
    except Exception:
        logger.warning(
            "Redis notification publish failed; falling back to in-process websocket delivery",
            exc_info=True,
        )

    await manager.send_notification_to_user(
        notification.user_id,
        payload,
    )
