from types import SimpleNamespace

import pytest
from fastapi import WebSocketDisconnect

from app.api.v1.websocket import websocket_endpoint


class _FakeWebSocket:
    def __init__(self, token=None, fail_after_first=False):
        self.query_params = {}
        if token is not None:
            self.query_params["token"] = token
        self.closed_with = None
        self.fail_after_first = fail_after_first
        self._receive_count = 0

    async def close(self, code: int):
        self.closed_with = code

    async def receive_text(self):
        self._receive_count += 1
        if self.fail_after_first and self._receive_count > 1:
            raise WebSocketDisconnect()
        return "ping"


@pytest.mark.asyncio
async def test_websocket_endpoint_rejects_missing_token():
    ws = _FakeWebSocket(token=None)
    await websocket_endpoint(ws, db=None)
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_websocket_endpoint_rejects_invalid_payload(monkeypatch):
    ws = _FakeWebSocket(token="x")
    monkeypatch.setattr("app.api.v1.websocket.decode_token", lambda _t: None)
    await websocket_endpoint(ws, db=None)
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_websocket_endpoint_rejects_non_numeric_user_id(monkeypatch):
    ws = _FakeWebSocket(token="x")
    monkeypatch.setattr("app.api.v1.websocket.decode_token", lambda _t: {"sub": "abc"})
    monkeypatch.setattr("app.api.v1.websocket.is_token_type", lambda *_args, **_kwargs: True)
    await websocket_endpoint(ws, db=None)
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_websocket_endpoint_rejects_inactive_user(monkeypatch):
    ws = _FakeWebSocket(token="x")
    monkeypatch.setattr("app.api.v1.websocket.decode_token", lambda _t: {"sub": "7"})
    monkeypatch.setattr("app.api.v1.websocket.is_token_type", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("app.api.v1.websocket.user_repo.get_active_by_id", lambda *_a, **_k: None)
    await websocket_endpoint(ws, db=None)
    assert ws.closed_with == 1008


@pytest.mark.asyncio
async def test_websocket_endpoint_connects_and_disconnects(monkeypatch):
    ws = _FakeWebSocket(token="x", fail_after_first=True)
    events = {"connected": False, "sent": 0, "disconnected": False}

    async def fake_connect(_ws, user_id: int):
        events["connected"] = user_id == 7

    async def fake_send_personal_message(_message, _ws):
        events["sent"] += 1

    def fake_disconnect(_ws):
        events["disconnected"] = True

    monkeypatch.setattr("app.api.v1.websocket.decode_token", lambda _t: {"sub": "7"})
    monkeypatch.setattr("app.api.v1.websocket.is_token_type", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "app.api.v1.websocket.user_repo.get_active_by_id",
        lambda *_a, **_k: SimpleNamespace(id=7, is_active=True),
    )
    monkeypatch.setattr("app.api.v1.websocket.manager.connect", fake_connect)
    monkeypatch.setattr("app.api.v1.websocket.manager.send_personal_message", fake_send_personal_message)
    monkeypatch.setattr("app.api.v1.websocket.manager.disconnect", fake_disconnect)

    await websocket_endpoint(ws, db=None)

    assert events["connected"] is True
    assert events["sent"] >= 1
    assert events["disconnected"] is True
