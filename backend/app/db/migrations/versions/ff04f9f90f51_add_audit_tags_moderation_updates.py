"""add audit tags moderation updates

Revision ID: ff04f9f90f51
Revises: 53c06d30f18b
Create Date: 2026-02-13 15:53:08.548420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff04f9f90f51'
down_revision: Union[str, Sequence[str], None] = '53c06d30f18b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "notifications",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("actor_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("title", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("entity_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("entity_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_notifications_user_id_users",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_notifications_actor_id_users",
        "notifications",
        "users",
        ["actor_id"],
        ["id"],
    )

    op.execute(
        """
        UPDATE notifications
        SET
            user_id = recipient_id,
            actor_id = sender_id,
            title = COALESCE(type, 'Notification'),
            entity_type = CASE
                WHEN comment_id IS NOT NULL THEN 'comment'
                WHEN thread_id IS NOT NULL THEN 'thread'
                ELSE 'system'
            END,
            entity_id = COALESCE(comment_id, thread_id, id),
            is_read = COALESCE(is_read, false)
        """
    )

    op.alter_column("notifications", "user_id", nullable=False)
    op.alter_column("notifications", "title", nullable=False)
    op.alter_column("notifications", "entity_type", nullable=False)
    op.alter_column("notifications", "entity_id", nullable=False)
    op.alter_column("notifications", "is_read", nullable=False)

    op.create_index(
        "ix_notifications_user_id",
        "notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_is_read",
        "notifications",
        ["is_read"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_created_at",
        "notifications",
        ["created_at"],
        unique=False,
    )

    op.drop_constraint(
        "notifications_recipient_id_fkey",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "notifications_sender_id_fkey",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "notifications_thread_id_fkey",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "notifications_comment_id_fkey",
        "notifications",
        type_="foreignkey",
    )
    op.drop_column("notifications", "recipient_id")
    op.drop_column("notifications", "sender_id")
    op.drop_column("notifications", "thread_id")
    op.drop_column("notifications", "comment_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "notifications",
        sa.Column("recipient_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("sender_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("thread_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("comment_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "notifications_recipient_id_fkey",
        "notifications",
        "users",
        ["recipient_id"],
        ["id"],
    )
    op.create_foreign_key(
        "notifications_sender_id_fkey",
        "notifications",
        "users",
        ["sender_id"],
        ["id"],
    )
    op.create_foreign_key(
        "notifications_thread_id_fkey",
        "notifications",
        "threads",
        ["thread_id"],
        ["id"],
    )
    op.create_foreign_key(
        "notifications_comment_id_fkey",
        "notifications",
        "comments",
        ["comment_id"],
        ["id"],
    )

    op.execute(
        """
        UPDATE notifications
        SET
            recipient_id = user_id,
            sender_id = actor_id,
            thread_id = CASE WHEN entity_type = 'thread' THEN entity_id ELSE NULL END,
            comment_id = CASE WHEN entity_type = 'comment' THEN entity_id ELSE NULL END
        """
    )

    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_constraint(
        "fk_notifications_actor_id_users",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_notifications_user_id_users",
        "notifications",
        type_="foreignkey",
    )
    op.drop_column("notifications", "entity_id")
    op.drop_column("notifications", "entity_type")
    op.drop_column("notifications", "title")
    op.drop_column("notifications", "actor_id")
    op.drop_column("notifications", "user_id")
