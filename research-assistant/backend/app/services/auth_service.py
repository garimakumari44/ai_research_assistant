from __future__ import annotations

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """
    Authentication and user business logic.

    Responsibilities:

        - Register users
        - Authenticate users
        - Generate access tokens
        - Generate refresh tokens
        - Refresh access tokens
        - Retrieve current users

    Database access is delegated to UserRepository.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.user_repository = UserRepository(
            session
        )

    # ========================================================================
    # REGISTER
    # ========================================================================

    async def register(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        """
        Register a new user.
        """

        email = email.strip().lower()

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required.",
            )

        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required.",
            )

        existing_user = (
            await self.user_repository.get_by_email(
                email
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(
                password
            ),
            is_active=True,
        )

        return await self.user_repository.create(
            user
        )

    # ========================================================================
    # LOGIN
    # ========================================================================

    async def login(
        self,
        email: str,
        password: str,
    ) -> dict[str, str]:
        """
        Authenticate a user and return a JWT token pair.
        """

        email = email.strip().lower()

        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user = (
            await self.user_repository.get_by_email(
                email
            )
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        password_valid = verify_password(
            password,
            user.hashed_password,
        )

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return self._create_token_pair(
            user.id
        )

    # ========================================================================
    # REFRESH
    # ========================================================================

    async def refresh(
        self,
        refresh_token: str,
    ) -> dict[str, str]:
        """
        Exchange a valid refresh token for a new
        access/refresh token pair.

        Refresh tokens are currently stateless JWTs.
        """

        if (
            not isinstance(refresh_token, str)
            or not refresh_token.strip()
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        refresh_token = refresh_token.strip()

        try:
            payload = decode_refresh_token(
                refresh_token
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        subject = payload.get(
            "sub"
        )

        if (
            subject is None
            or str(subject).strip() == ""
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        try:
            user_id = int(subject)

        except (
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        user = (
            await self.user_repository.get_by_id(
                user_id
            )
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user no longer exists.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return self._create_token_pair(
            user.id
        )

    # ========================================================================
    # TOKEN PAIR
    # ========================================================================

    @staticmethod
    def _create_token_pair(
        user_id: int,
    ) -> dict[str, str]:
        """
        Create a new access/refresh token pair.

        Both tokens use the same user ID as their JWT subject.

        Access token:
            type = access

        Refresh token:
            type = refresh
        """

        if user_id is None or user_id <= 0:
            raise ValueError(
                "Cannot create tokens for an invalid user ID."
            )

        access_token = create_access_token(
            subject=user_id
        )

        refresh_token = create_refresh_token(
            subject=user_id
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ========================================================================
    # CURRENT USER
    # ========================================================================

    async def get_user(
        self,
        user_id: int,
    ) -> User | None:
        """
        Retrieve a user by primary key.
        """

        if user_id <= 0:
            return None

        return await self.user_repository.get_by_id(
            user_id
        )