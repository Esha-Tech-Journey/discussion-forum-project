from app.websocket.manager import manager
from app.websocket.events import WSEvents
from app.integrations.redis_client import (
    redis_client
)
from app.core.constants import RedisChannels
from app.websocket.notifications_handler import (
    dispatch_notification_event,
)


# ==============================
# Comment Event
# ==============================

async def broadcast_new_comment(comment):

    message = {
        "event": WSEvents.NEW_COMMENT,
        "data": {
            "comment_id": comment.id,
            "thread_id": comment.thread_id,
            "content": comment.content,
        }
    }

    await manager.broadcast(message)
    await redis_client.publish(
        RedisChannels.COMMENTS,
        message
    )


# ==============================
# Thread Event
# ==============================

async def broadcast_new_thread(
    thread,
    action: str = "created",
):

    message = {
        "event": WSEvents.NEW_THREAD,
        "data": {
            "action": action,
            "thread": {
                "id": thread.id,
                "title": thread.title,
            },
        }
    }

    await manager.broadcast(message)
    await redis_client.publish(
        RedisChannels.THREADS,
        message
    )


# ==============================
# Like Event
# ==============================

async def broadcast_new_like(
    thread_id=None,
    comment_id=None,
    like_count=None,
    action="updated",
):

    message = {
        "event": WSEvents.NEW_LIKE,
        "data": {
            "thread_id": thread_id,
            "comment_id": comment_id,
            "like_count": like_count,
            "action": action,
        }
    }

    await manager.broadcast(message)
    await redis_client.publish(
        RedisChannels.LIKES,
        message
    )


# ==============================
# Notification Event
# ==============================

async def broadcast_notification(
    notification
):
    await dispatch_notification_event(
        notification
    )


# ==============================
# User Event
# ==============================

async def broadcast_new_user(
    user,
    action: str = "created",
):

    message = {
        "event": WSEvents.NEW_USER,
        "data": {
            "action": action,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "is_active": user.is_active,
                "created_at": str(user.created_at),
                "roles": [
                    {
                        "id": role.id,
                        "role_name": role.role_name,
                    }
                    for role in (user.roles or [])
                ],
            },
        },
    }

    await manager.broadcast(message)
    await redis_client.publish(
        RedisChannels.USERS,
        message,
    )


# ==============================
# Moderation Event
# ==============================

async def broadcast_moderation_review(
    review,
    action: str = "created",
):

    message = {
        "event": WSEvents.MODERATION_REVIEW,
        "data": {
            "action": action,
            "review": {
                "id": review.id,
                "content_type": review.content_type,
                "thread_id": review.thread_id,
                "comment_id": review.comment_id,
                "reason": review.reason,
                "reviewer_id": review.reviewer_id,
                "status": review.status,
                "action_taken": review.action_taken,
                "created_at": str(review.created_at),
                "updated_at": str(review.updated_at),
            },
        },
    }

    await manager.broadcast(message)
    await redis_client.publish(
        RedisChannels.MODERATION,
        message,
    )
