from fastapi import APIRouter

from app.api.v1 import auth, comments, likes, mentions, moderation, notifications, search, threads, users, websocket


api_router = APIRouter(
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    }
)

# Auth routes
api_router.include_router(auth.router)
api_router.include_router(threads.router)
api_router.include_router(comments.router)
api_router.include_router(likes.router)
api_router.include_router(mentions.router)
api_router.include_router(notifications.router)
api_router.include_router(moderation.router)
api_router.include_router(search.router)
api_router.include_router(users.router)
api_router.include_router(websocket.router)
