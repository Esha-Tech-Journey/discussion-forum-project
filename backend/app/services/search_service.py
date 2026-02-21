from sqlalchemy.orm import Session

from app.repositories.comment import CommentRepository
from app.repositories.thread import ThreadRepository
from app.services.thread_service import ThreadService


class SearchService:

    thread_repo = ThreadRepository()
    # Backward-compatible alias used by existing tests and wrappers.
    repo = thread_repo
    comment_repo = CommentRepository()

    @staticmethod
    def _serialize_comment(comment) -> dict:
        likes = list(comment.likes or [])
        return {
            "id": comment.id,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "content": comment.content,
            "thread_id": comment.thread_id,
            "author_id": comment.author_id,
            "author": (
                {
                    "id": comment.author.id,
                    "name": comment.author.name,
                    "email": comment.author.email,
                    "avatar_url": comment.author.avatar_url,
                }
                if comment.author
                else None
            ),
            "parent_comment_id": comment.parent_comment_id,
            "like_count": len(likes),
            "user_has_liked": False,
            "is_deleted": comment.is_deleted,
        }

    # ==============================
    # Search Threads
    # ==============================
    @classmethod
    def search_threads(
        cls,
        db: Session,
        keyword: str,
        page: int = 1,
        size: int = 20,
        search_in: str = "all",
        sort_by: str = "relevance",
    ):

        if not keyword:
            return {
                "results": [],
                "total": 0
            }

        results = cls.repo.search_threads(
            db,
            keyword,
            search_in=search_in,
        )
        serialized = []
        for thread in results:
            try:
                serialized.append(
                    ThreadService._serialize_thread(thread, None)
                )
            except AttributeError:
                serialized.append({"id": getattr(thread, "id", None)})

        if sort_by == "recent":
            serialized.sort(
                key=lambda item: item.get("created_at") or "",
                reverse=True,
            )
        elif sort_by == "popular":
            serialized.sort(
                key=lambda item: (
                    int(item.get("like_count") or 0),
                    int(item.get("comment_count") or 0),
                ),
                reverse=True,
            )
        total = len(serialized)
        start = (page - 1) * size
        end = start + size

        return {
            "results": serialized[start:end],
            "total": total
        }

    @classmethod
    def search_comments(
        cls,
        db: Session,
        keyword: str,
        page: int = 1,
        size: int = 20,
    ):
        if not keyword:
            return {
                "results": [],
                "total": 0
            }

        results = cls.comment_repo.search_comments(
            db,
            keyword,
        )
        serialized = [
            cls._serialize_comment(comment)
            for comment in results
        ]
        total = len(serialized)
        start = (page - 1) * size
        end = start + size
        return {
            "results": serialized[start:end],
            "total": total
        }
