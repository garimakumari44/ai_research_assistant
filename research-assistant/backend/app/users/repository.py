"""
User repository.

Handles all database operations related to users.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    """
    Repository for user database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # ==========================================================
    # Queries
    # ==========================================================

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        """
        Retrieve a user by ID.
        """

        return await self.session.get(
            User,
            user_id,
        )

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email.
        """

        result = await self.session.execute(
            select(User).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Return a paginated list of users.
        """

        result = await self.session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    # ==========================================================
    # Create
    # ==========================================================

    async def create(
        self,
        user: User,
    ) -> User:
        """
        Create a new user.
        """

        self.session.add(user)

        await self.session.commit()

        await self.session.refresh(user)

        return user

    # ==========================================================
    # Update
    # ==========================================================

    async def update(
        self,
        user: User,
    ) -> User:
        """
        Save changes to a user.
        """

        await self.session.commit()

        await self.session.refresh(user)

        return user

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete(
        self,
        user: User,
    ) -> None:
        """
        Delete a user.
        """

        await self.session.delete(user)

        await self.session.commit()

    # ==========================================================
    # Status
    # ==========================================================

    async def activate(
        self,
        user: User,
    ) -> User:
        """
        Activate a user account.
        """

        user.is_active = True

        return await self.update(user)

    async def deactivate(
        self,
        user: User,
    ) -> User:
        """
        Deactivate a user account.
        """

        user.is_active = False

        return await self.update(user)

    # ==========================================================
    # Utility
    # ==========================================================

    async def exists(
        self,
        email: str,
    ) -> bool:
        """
        Check whether a user exists.
        """

        return (
            await self.get_by_email(email)
        ) is not None

    async def count(
        self,
    ) -> int:
        """
        Return total number of users.
        """

        result = await self.session.execute(
            select(User)
        )

        return len(result.scalars().all())