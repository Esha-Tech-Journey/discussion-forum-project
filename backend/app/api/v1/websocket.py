from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.websocket.manager import manager
from app.core.security import decode_token, is_token_type
from app.db.session import get_db
from app.repositories.user import UserRepository


router = APIRouter()
user_repo = UserRepository()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_token(token)

    if (
        not payload
        or "sub" not in payload
        or not is_token_type(payload, "access")
    ):
        await websocket.close(code=1008)
        return

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        await websocket.close(code=1008)
        return

    user = user_repo.get_active_by_id(db, user_id)

    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive client messages if needed
            data = await websocket.receive_text()

            # Echo / heartbeat (optional)
            await manager.send_personal_message(
                {"message": "Received"},
                websocket
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
