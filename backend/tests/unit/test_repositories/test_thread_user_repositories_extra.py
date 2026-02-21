from app.core.constants import Roles
from app.models.role import Role
from app.models.tag import Tag
from app.repositories.comment import CommentRepository
from app.repositories.like import LikeRepository
from app.repositories.role import RoleRepository
from app.repositories.thread import ThreadRepository
from app.repositories.user import UserRepository


def _create_roles(db):
    role_repo = RoleRepository()
    for role_name in (Roles.ADMIN, Roles.MODERATOR, Roles.MEMBER):
        if role_repo.get_by_name(db, role_name) is None:
            db.add(Role(role_name=role_name))
    db.commit()


def _create_user_with_name(db, email: str, name: str):
    return UserRepository().create(
        db,
        {"email": email, "password_hash": "hashed", "name": name},
    )


def test_thread_repository_custom_queries(db):
    user = _create_user_with_name(db, "thread-extra@example.com", "Threader")
    repo = ThreadRepository()
    tag = Tag(name="architecture")
    db.add(tag)
    db.commit()
    db.refresh(tag)

    t1 = repo.create(
        db,
        {"title": "Caching strategy", "description": "Redis and API cache", "author_id": user.id},
    )
    t1.tags.append(tag)
    db.commit()

    t2 = repo.create(
        db,
        {"title": "To delete", "description": "Deleted thread", "author_id": user.id},
    )

    assert repo.get_by_id(db, t1.id).id == t1.id
    assert repo.count_active_threads(db) >= 2
    assert len(repo.get_active_threads(db)) >= 2
    assert any(thread.id == t1.id for thread in repo.search_threads(db, "architecture"))

    repo.soft_delete(db, t2)
    assert repo.get_by_id(db, t2.id).is_deleted is True


def test_user_repository_extended_queries(db):
    _create_roles(db)
    role_repo = RoleRepository()
    admin_role = role_repo.get_by_name(db, Roles.ADMIN)
    member_role = role_repo.get_by_name(db, Roles.MEMBER)
    user_repo = UserRepository()
    thread_repo = ThreadRepository()
    like_repo = LikeRepository()
    comment_repo = CommentRepository()

    admin = user_repo.create_with_roles(
        db,
        {"email": "admin-repo@example.com", "password_hash": "hashed", "name": "Admin"},
        [admin_role],
    )
    member = user_repo.create_with_roles(
        db,
        {"email": "member-repo@example.com", "password_hash": "hashed", "name": "Member"},
        [member_role],
    )

    assert user_repo.get_by_names(db, []) == []
    assert len(user_repo.get_by_names(db, ["Admin", "Member"])) == 2

    thread = thread_repo.create(
        db,
        {"title": "Repo user list", "description": "for stats", "author_id": member.id},
    )
    comment = comment_repo.create(
        db,
        {"content": "nice", "thread_id": thread.id, "author_id": admin.id},
    )
    like_repo.create(db, {"user_id": admin.id, "thread_id": thread.id})
    like_repo.create(db, {"user_id": member.id, "comment_id": comment.id})

    users_page, total = user_repo.list_users(db, page=1, size=10, q="repo")
    assert total >= 2
    assert len(users_page) >= 2

    member_stats, total_member_stats = user_repo.list_users_by_role_with_stats(
        db,
        role_name=Roles.MEMBER,
        page=1,
        size=10,
        q="member",
    )
    assert total_member_stats >= 1
    assert member_stats[0]["thread_count"] >= 1

    moderator_stats, _ = user_repo.list_users_by_role_with_stats(
        db,
        role_name=Roles.MODERATOR,
        page=1,
        size=10,
        q="no-match",
    )
    assert moderator_stats == []

    suggestions = user_repo.suggest_users(
        db,
        q="M",
        limit=5,
        exclude_user_id=admin.id,
    )
    assert all(user.id != admin.id for user in suggestions)

