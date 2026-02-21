from app.services.thread_service import ThreadService
from app.schemas.thread import ThreadCreate


def test_create_thread(db):

    payload = ThreadCreate(
        title="Test Thread",
        description="Test Description"
    )

    thread = ThreadService.create_thread(
        db,
        payload,
        user_id=1
    )

    assert thread.title == "Test Thread"
    assert thread.author_id == 1
