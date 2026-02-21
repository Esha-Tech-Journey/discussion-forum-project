import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.constants import RedisChannels
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
)
from app.websocket.manager import manager
from app.db.session import SessionLocal
from app.services.bootstrap_service import BootstrapService

from app.core.logging import setup_logging

setup_logging()

OPENAPI_TAGS = [
    {"name": "Auth", "description": "Authentication and profile endpoints."},
    {"name": "Threads", "description": "Thread CRUD and listing."},
    {"name": "Comments", "description": "Comment and reply operations."},
    {"name": "Likes", "description": "Like and unlike operations."},
    {"name": "Mentions", "description": "Mention retrieval operations."},
    {"name": "Notifications", "description": "Notification inbox operations."},
    {"name": "Moderation", "description": "Moderation review workflows."},
    {"name": "Search", "description": "Thread and comment search endpoints."},
    {"name": "Users", "description": "Admin/member user management APIs."},
]


async def start_redis_listener():
    db = SessionLocal()
    try:
        BootstrapService.ensure_roles_and_admin(db)
    finally:
        db.close()

    return [
        asyncio.create_task(manager.listen_to_channel(RedisChannels.COMMENTS)),
        asyncio.create_task(manager.listen_to_channel(RedisChannels.THREADS)),
        asyncio.create_task(manager.listen_to_channel(RedisChannels.LIKES)),
        asyncio.create_task(manager.listen_to_channel(RedisChannels.NOTIFICATIONS)),
        asyncio.create_task(manager.listen_to_channel(RedisChannels.USERS)),
        asyncio.create_task(manager.listen_to_channel(RedisChannels.MODERATION)),
    ]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tasks = await start_redis_listener()
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(
    title="Advanced Real-Time Discussion Forum API",
    description=(
        "Backend API for the discussion forum supporting JWT auth, RBAC, "
        "threads, nested comments, likes, notifications, moderation, and websocket updates."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    servers=[
        {"url": "http://localhost:8000", "description": "Local backend"},
        {"url": "http://localhost", "description": "Nginx reverse proxy"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    AppException,
    app_exception_handler
)


# Register API routes
app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/health")
def health():
    return {"status": "ok"}
