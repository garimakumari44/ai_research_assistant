"""
User service.

Contains business logic for user management.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import (
    hash_password,
    validate_password,
    verify_password,
)
from app.auth.roles import UserRole
from app.users.repository import UserRepository


class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""


class EmailAlreadyExistsError(Exception):
    """Raised when an email already exists."""


class InvalidPasswordError(Exception):
    """Raised when password validation fails."""


class UserService:
    """
    User management business logic.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:

        self.repository = UserRepository(session)

    # ==========================================================
    # Read
    # ==========================================================

    async def get_user(
        self,
        user_id: int,
    ):
        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError(
                f"User {user_id} not found."
            )

        return user

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ):
        return await self.repository.list_users(
            skip=skip,
            limit=limit,
        )

    # ==========================================================
    # Profile
    # ==========================================================

    async def update_profile(
        self,
        user_id: int,
        *,
        full_name: str | None = None,
        email: str | None = None,
    ):

        user = await self.get_user(user_id)

        if email is not None and email != user.email:

            existing = await self.repository.get_by_email(
                email
            )

            if existing:
                raise EmailAlreadyExistsError(
                    "Email already exists."
                )

            user.email = email

        if full_name is not None:
            user.full_name = full_name

        return await self.repository.update(user)

    # ==========================================================
    # Password
    # ==========================================================

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ):

        user = await self.get_user(user_id)

        if not verify_password(
            current_password,
            user.hashed_password,
        ):
            raise InvalidPasswordError(
                "Current password is incorrect."
            )

        valid, message = validate_password(
            new_password
        )

        if not valid:
            raise InvalidPasswordError(message)

        user.hashed_password = hash_password(
            new_password
        )

        return await self.repository.update(user)

    # ==========================================================
    # Roles
    # ==========================================================

    async def change_role(
        self,
        user_id: int,
        role: UserRole,
    ):

        user = await self.get_user(user_id)

        user.role = role.value

        return await self.repository.update(user)

    # ==========================================================
    # Activation
    # ==========================================================

    async def activate(
        self,
        user_id: int,
    ):

        user = await self.get_user(user_id)

        return await self.repository.activate(user)

    async def deactivate(
        self,
        user_id: int,
    ):

        user = await self.get_user(user_id)

        return await self.repository.deactivate(user)

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete(
        self,
        user_id: int,
    ):

        user = await self.get_user(user_id)

        await self.repository.delete(user)

        return True