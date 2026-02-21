import sys
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.constants import Roles
from app.db.session import SessionLocal
from app.models.role import Role


def seed_roles(db: Session):
    """
    Seed default system roles.

    Creates:
    - ADMIN
    - MODERATOR
    - MEMBER
    """

    engine = db.get_bind()
    inspector = inspect(engine)

    if not inspector.has_table("roles"):
        Role.__table__.create(bind=engine, checkfirst=True)

    existing_roles = {
        row[0]
        for row in db.execute(text("SELECT role_name FROM roles")).all()
    }

    default_roles = [
        Roles.ADMIN,
        Roles.MODERATOR,
        Roles.MEMBER,
    ]

    for role_name in default_roles:
        if role_name not in existing_roles:
            db.execute(
                text("INSERT INTO roles (role_name) VALUES (:role_name)"),
                {"role_name": role_name},
            )

    db.commit()
    print("Roles seeded successfully.")


def run():
    """
    Script entry point.
    """
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
