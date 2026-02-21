from sqlalchemy.orm import Session

from app.repositories.mention import MentionRepository
from app.repositories.user import UserRepository
from app.utils.mention_parser import extract_usernames


class MentionService:

    repo = MentionRepository()
    user_repo = UserRepository()

    # ==============================
    # Process Mentions
    # ==============================
    @classmethod
    def process_mentions(
        cls,
        db: Session,
        content: str,
        thread_id: int = None,
        comment_id: int = None
    ):
        """
        Extract @mentions and store them.
        """

        usernames = extract_usernames(content)

        if not usernames:
            return []

        users = cls.user_repo.get_by_names(
            db,
            usernames,
        )

        if not users:
            return []

        mention_data = []

        for user in users:
            mention_data.append({
                "mentioned_user_id": user.id,
                "thread_id": thread_id,
                "comment_id": comment_id,
            })

        cls.repo.bulk_create(db, mention_data)

        return users

    @classmethod
    def get_user_mentions(
        cls,
        db: Session,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ):
        items, total = cls.repo.list_user_mentions(
            db,
            user_id=user_id,
            page=page,
            size=size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
        }
