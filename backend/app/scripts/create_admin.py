"""
Create Initial Administrator.

Usage:

python -m app.scripts.create_admin
"""

from __future__ import annotations

import getpass

from sqlalchemy import select

from app.auth.security import security
from app.database.database import SessionLocal
from app.models.user import User
from app.models.user import UserRole


def main() -> None:

    db = SessionLocal()

    try:

        print("=" * 60)
        print("Athena Administrator Setup")
        print("=" * 60)

        username = input("Username : ").strip()

        email = input("Email    : ").strip()

        full_name = input("Full Name: ").strip()

        password = getpass.getpass("Password : ")

        existing = db.scalar(

            select(User).where(

                (User.username == username)

                | (User.email == email)

            )

        )

        if existing:

            print()

            print("User already exists.")

            return

        admin = User(

            username=username,

            email=email,

            full_name=full_name,

            password_hash=security.hash_password(
                password
            ),

            role=UserRole.ADMIN,

            is_active=True,

            is_verified=True,

            is_superuser=True,

        )

        db.add(admin)

        db.commit()

        db.refresh(admin)

        print()

        print("Administrator created successfully.")

        print(f"User ID : {admin.id}")

    finally:

        db.close()


if __name__ == "__main__":

    main()