
from __future__ import annotations

from math import ceil
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.collection_repository import CollectionRepository
from app.schemas.collections import (
    CollectionCreate,
    CollectionUpdate,
)


class CollectionService:
    """
    Business/application layer for collections.

    The service receives the authenticated user ID from the API layer
    and delegates database operations to CollectionRepository.

    Ownership checks are always performed using the authenticated user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CollectionRepository(db)

    # ========================================================================
    # Helpers
    # ========================================================================

    @staticmethod
    def _user_id(
        user_id: str | int | None,
    ) -> int:
        """
        Convert the authenticated JWT subject into an integer user ID.
        """

        if user_id is None:
            raise ValueError(
                "Authentication required."
            )

        try:
            return int(user_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid authenticated user ID."
            ) from exc

    @staticmethod
    def _collection_id(
        collection_id: int | str,
    ) -> int:
        """
        Normalize collection IDs.

        The current database/API contract uses integer collection IDs.
        """

        try:
            value = int(collection_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid collection ID."
            ) from exc

        if value <= 0:
            raise ValueError(
                "Collection ID must be greater than zero."
            )

        return value

    @staticmethod
    def _paper_id(
        paper_id: int | str,
    ) -> int:
        """
        Normalize paper IDs.
        """

        try:
            value = int(paper_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid paper ID."
            ) from exc

        if value <= 0:
            raise ValueError(
                "Paper ID must be greater than zero."
            )

        return value

    # ========================================================================
    # Collections
    # ========================================================================

    async def list_collections(
        self,
        *,
        user_id: str | int,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        archived: bool | None = None,
    ) -> dict[str, Any]:

        db_user_id = self._user_id(user_id)

        collections, total = (
            await self.repository.list_collections(
                user_id=db_user_id,
                page=page,
                page_size=page_size,
                search=search,
                archived=archived,
            )
        )

        return {
            "items": collections,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (
                ceil(total / page_size)
                if total
                else 0
            ),
        }

    # ========================================================================
    # Create collection
    # ========================================================================

    async def create_collection(
        self,
        *,
        user_id: str | int,
        payload: CollectionCreate,
    ):

        db_user_id = self._user_id(user_id)

        name = payload.name.strip()

        if not name:
            raise ValueError(
                "Collection name is required."
            )

        description = payload.description

        if description is not None:
            description = description.strip()

            if not description:
                description = None

        return await self.repository.create_collection(
            user_id=db_user_id,
            name=name,
            description=description,
            archived=payload.archived,
        )

    # ========================================================================
    # Get collection
    # ========================================================================

    async def get_collection(
        self,
        *,
        user_id: str | int,
        collection_id: int | str,
    ):

        db_user_id = self._user_id(user_id)
        db_collection_id = self._collection_id(
            collection_id
        )

        return await self.repository.get_collection(
            collection_id=db_collection_id,
            user_id=db_user_id,
        )

    # ========================================================================
    # Update collection
    # ========================================================================

    async def update_collection(
        self,
        *,
        user_id: str | int,
        collection_id: int | str,
        payload: CollectionUpdate,
    ):

        db_user_id = self._user_id(user_id)
        db_collection_id = self._collection_id(
            collection_id
        )

        collection = await self.repository.get_collection(
            collection_id=db_collection_id,
            user_id=db_user_id,
        )

        if collection is None:
            return None

        update_data = payload.model_dump(
            exclude_unset=True,
        )

        # --------------------------------------------------------------------
        # Name
        # --------------------------------------------------------------------

        if "name" in update_data:
            name = update_data["name"]

            if name is None:
                raise ValueError(
                    "Collection name cannot be null."
                )

            name = name.strip()

            if not name:
                raise ValueError(
                    "Collection name cannot be empty."
                )

            update_data["name"] = name

        # --------------------------------------------------------------------
        # Description
        # --------------------------------------------------------------------

        if "description" in update_data:
            description = update_data["description"]

            if isinstance(description, str):
                description = description.strip()

                update_data["description"] = (
                    description
                    if description
                    else None
                )

        return await self.repository.update_collection(
            collection=collection,
            data=update_data,
        )

    # ========================================================================
    # Delete collection
    # ========================================================================

    async def delete_collection(
        self,
        *,
        user_id: str | int,
        collection_id: int | str,
    ) -> bool:

        db_user_id = self._user_id(user_id)
        db_collection_id = self._collection_id(
            collection_id
        )

        collection = await self.repository.get_collection(
            collection_id=db_collection_id,
            user_id=db_user_id,
        )

        if collection is None:
            return False

        await self.repository.delete_collection(
            collection=collection,
        )

        return True

    # ========================================================================
    # Collection Items
    # ========================================================================

    async def list_collection_items(
        self,
        *,
        user_id: str | int,
        collection_id: int | str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any] | None:

        db_user_id = self._user_id(user_id)
        db_collection_id = self._collection_id(
            collection_id
        )

        # Ownership check first.
        collection = await self.repository.get_collection(
            collection_id=db_collection_id,
            user_id=db_user_id,
        )

        if collection is None:
            return None

        items, total = (
            await self.repository.list_collection_items(
                collection_id=db_collection_id,
                page=page,
                page_size=page_size,
            )
        )

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (
                ceil(total / page_size)
                if total
                else 0
            ),
        }

    # ========================================================================
    # Add collection item
    # ========================================================================

    async def add_collection_item(
        self,
        *,
        user_id: str | int,
        collection_id: int | str,
        paper_id: int | str,
    ):

        db_user_id = self._user_id(user_id)

        db_collection_id = self._collection_id(
            collection_id
        )

        db_paper_id = self._paper_id(
            paper_id
        )

        # Ownership check first.
        collection = await self.repository.get_collection(
            collection_id=db_collection_id,
            user_id=db_user_id,
        )

        if collection is None:
            return None

        return await self.repository.add_collection_item(
            collection_id=db_collection_id,
            paper_id=db_paper_id,
        )

    # ========================================================================
    # Remove collection item
    # ========================================================================

    async def remove_collection_item(
        self,
        *,
        user_id: str | int,
        collection_id: int | str,
        paper_id: int | str,
    ) -> bool:

        db_user_id = self._user_id(user_id)

        db_collection_id = self._collection_id(
            collection_id
        )

        db_paper_id = self._paper_id(
            paper_id
        )

        # Ownership check first.
        collection = await self.repository.get_collection(
            collection_id=db_collection_id,
            user_id=db_user_id,
        )

        if collection is None:
            return False

        # IMPORTANT:
        # No trailing comma here.
        #
        # The old code:
        #
        # return await repository.remove_collection_item(...),
        #
        # returned a tuple: (True,)
        #
        # instead of:
        #
        # True
        return await self.repository.remove_collection_item(
            collection_id=db_collection_id,
            paper_id=db_paper_id,
        )

