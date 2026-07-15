"""
Athena Security Utilities.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from jose import JWTError
from jose import jwt
from passlib.context import CryptContext

from app.core.settings import settings

# ==========================================================
# Password Hashing
# ==========================================================

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


class Security:
    """
    Authentication and JWT helper utilities.
    """

    # ======================================================
    # Password
    # ======================================================

    @staticmethod
    def hash_password(
        password: str,
    ) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        return pwd_context.verify(
            plain_password,
            hashed_password,
        )

    # ======================================================
    # Internal JWT Creator
    # ======================================================

    @staticmethod
    def _create_token(
        *,
        subject: str,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:

        now = datetime.now(timezone.utc)

        payload: dict[str, Any] = {

            "sub": subject,

            "type": token_type,

            "iat": now,

            "exp": now + expires_delta,

        }

        return jwt.encode(

            payload,

            settings.SECRET_KEY,

            algorithm=settings.ALGORITHM,

        )

    # ======================================================
    # Access Token
    # ======================================================

    @classmethod
    def create_access_token(
        cls,
        subject: str,
    ) -> str:

        return cls._create_token(

            subject=subject,

            token_type="access",

            expires_delta=timedelta(

                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,

            ),

        )

    # ======================================================
    # Refresh Token
    # ======================================================

    @classmethod
    def create_refresh_token(
        cls,
        subject: str,
    ) -> str:

        return cls._create_token(

            subject=subject,

            token_type="refresh",

            expires_delta=timedelta(

                days=settings.REFRESH_TOKEN_EXPIRE_DAYS,

            ),

        )

    # ======================================================
    # Decode
    # ======================================================

    @staticmethod
    def decode_token(
        token: str,
    ) -> dict[str, Any]:

        return jwt.decode(

            token,

            settings.SECRET_KEY,

            algorithms=[settings.ALGORITHM],

        )

    # ======================================================
    # Subject
    # ======================================================

    @classmethod
    def get_subject(
        cls,
        token: str,
    ) -> str:

        payload = cls.decode_token(token)

        subject = payload.get("sub")

        if subject is None:

            raise JWTError("Missing token subject.")

        return str(subject)

    # ======================================================
    # Token Type
    # ======================================================

    @classmethod
    def get_token_type(
        cls,
        token: str,
    ) -> str:

        payload = cls.decode_token(token)

        token_type = payload.get("type")

        if token_type is None:

            raise JWTError("Missing token type.")

        return str(token_type)


security = Security()