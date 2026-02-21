from app import main
import pytest


def test_health_endpoint_function():
    assert main.health() == {"status": "ok"}


def test_startup_listener_registers_tasks(monkeypatch):
    calls = {"bootstrap": 0, "channels": [], "tasks": 0, "closed": 0}

    class FakeSession:
        def close(self):
            calls["closed"] += 1

    async def fake_listener(channel: str):
        calls["channels"].append(channel)

    def fake_create_task(coro):
        calls["tasks"] += 1
        coro.close()
        return None

    monkeypatch.setattr(main, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(
        main.BootstrapService,
        "ensure_roles_and_admin",
        lambda _db: calls.__setitem__("bootstrap", calls["bootstrap"] + 1),
    )
    monkeypatch.setattr(main.manager, "listen_to_channel", fake_listener)
    monkeypatch.setattr(main.asyncio, "create_task", fake_create_task)

    import asyncio

    asyncio.run(main.start_redis_listener())

    assert calls["bootstrap"] == 1
    assert calls["tasks"] == 6
    assert calls["closed"] == 1


@pytest.mark.asyncio
async def test_lifespan_cancels_startup_tasks(monkeypatch):
    calls = {"cancelled": 0}

    class FakeTask:
        def cancel(self):
            calls["cancelled"] += 1

    async def fake_gather(*_args, **_kwargs):
        return []

    async def fake_start():
        return [FakeTask(), FakeTask(), FakeTask(), FakeTask(), FakeTask(), FakeTask()]

    monkeypatch.setattr(main, "start_redis_listener", fake_start)
    monkeypatch.setattr(main.asyncio, "gather", fake_gather)

    async with main.lifespan(main.app):
        pass

    assert calls["cancelled"] == 6
