from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    """
    Repository responsible for User persistence.

    Database access is kept inside this repository.
    Authentication and business logic belong in the service layer.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================
    # GET BY ID
    # =========================================================

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()

    # =========================================================
    # GET BY EMAIL
    # =========================================================

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none()

    # =========================================================
    # EXISTS BY EMAIL
    # =========================================================

    async def exists_by_email(
        self,
        email: str,
    ) -> bool:
        result = await self.session.execute(
            select(User.id).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none() is not None

    # =========================================================
    # CREATE
    # =========================================================

    async def create(
        self,
        user: User,
    ) -> User:
        """
        Create and persist a new user.
        """

        self.session.add(user)

        # Flush first so SQLAlchemy obtains the generated ID.
        await self.session.flush()

        # Commit the transaction so the user is permanently
        # stored in PostgreSQL.
        await self.session.commit()

        # Refresh the object with database-generated values.
        await self.session.refresh(user)

        return user

    # =========================================================
    # UPDATE
    # =========================================================

    async def update(
        self,
        user: User,
    ) -> User:
        """
        Update and persist an existing user.
        """

        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    # =========================================================
    # DELETE
    # =========================================================

    async def delete(
        self,
        user: User,
    ) -> None:
        """
        Delete a user permanently.
        """

        await self.session.delete(user)

        await self.session.commit()

    # =========================================================
    # LIST USERS
    # =========================================================

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """
        Return a paginated list of users.
        """

        result = await self.session.execute(
            select(User)
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()