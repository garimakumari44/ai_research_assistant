from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.collection import Collection
from app.db.models.collection_item import CollectionItem
from app.db.models.paper import (
    Paper,
    PaperAuthor,
    PaperTopic,
)


class CollectionRepository:
    """
    Database access layer for collections and collection items.

    Responsibilities:
    - Query collections
    - Create/update/delete collections
    - Query collection items
    - Add/remove papers from collections

    Authentication and application-level business rules belong
    to the service layer.

    Important:
    This repository uses AsyncSession and therefore eagerly loads
    relationships that may be accessed during FastAPI/Pydantic
    response serialization.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    # ========================================================================
    # Shared relationship loading
    # ========================================================================

    @staticmethod
    def _collection_load_options():
        """
        Eager-load the complete collection response graph.

        Collection
            └── items
                └── Paper
                    ├── Venue
                    ├── Author links -> Author
                    └── Topic links -> Topic

        This prevents MissingGreenlet errors during response serialization.
        """

        return (
            # ----------------------------------------------------------------
            # Collection -> items
            # ----------------------------------------------------------------
            selectinload(
                Collection.items,
            ),

            # ----------------------------------------------------------------
            # Collection -> items -> paper -> venue
            # ----------------------------------------------------------------
            selectinload(
                Collection.items,
            )
            .selectinload(
                CollectionItem.paper,
            )
            .selectinload(
                Paper.venue,
            ),

            # ----------------------------------------------------------------
            # Collection -> items -> paper -> authors
            # ----------------------------------------------------------------
            selectinload(
                Collection.items,
            )
            .selectinload(
                CollectionItem.paper,
            )
            .selectinload(
                Paper.author_links,
            )
            .selectinload(
                PaperAuthor.author,
            ),

            # ----------------------------------------------------------------
            # Collection -> items -> paper -> topics
            # ----------------------------------------------------------------
            selectinload(
                Collection.items,
            )
            .selectinload(
                CollectionItem.paper,
            )
            .selectinload(
                Paper.topic_links,
            )
            .selectinload(
                PaperTopic.topic,
            ),
        )

    @staticmethod
    def _collection_item_load_options():
        """
        Eager-load the complete CollectionItem response graph.

        CollectionItem
            └── Paper
                ├── Venue
                ├── Author links -> Author
                └── Topic links -> Topic
        """

        return (
            # ----------------------------------------------------------------
            # Item -> Paper -> Venue
            # ----------------------------------------------------------------
            selectinload(
                CollectionItem.paper,
            ).selectinload(
                Paper.venue,
            ),

            # ----------------------------------------------------------------
            # Item -> Paper -> Authors
            # ----------------------------------------------------------------
            selectinload(
                CollectionItem.paper,
            )
            .selectinload(
                Paper.author_links,
            )
            .selectinload(
                PaperAuthor.author,
            ),

            # ----------------------------------------------------------------
            # Item -> Paper -> Topics
            # ----------------------------------------------------------------
            selectinload(
                CollectionItem.paper,
            )
            .selectinload(
                Paper.topic_links,
            )
            .selectinload(
                PaperTopic.topic,
            ),
        )

    # ========================================================================
    # Collections
    # ========================================================================

    async def list_collections(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        archived: bool | None = None,
    ) -> tuple[list[Collection], int]:
        """
        Return paginated collections belonging to a user.
        """

        page = max(int(page), 1)
        page_size = max(int(page_size), 1)

        # --------------------------------------------------------------------
        # Base collection query
        # --------------------------------------------------------------------

        query = (
            select(Collection)
            .where(
                Collection.user_id == user_id,
            )
            .options(
                *self._collection_load_options(),
            )
        )

        # --------------------------------------------------------------------
        # Count query
        # --------------------------------------------------------------------

        count_query = select(
            func.count(Collection.id),
        ).where(
            Collection.user_id == user_id,
        )

        # --------------------------------------------------------------------
        # Search
        # --------------------------------------------------------------------

        if search:
            search_value = search.strip()

            if search_value:
                pattern = f"%{search_value}%"

                search_filter = or_(
                    Collection.name.ilike(pattern),
                    Collection.description.ilike(pattern),
                )

                query = query.where(search_filter)
                count_query = count_query.where(search_filter)

        # --------------------------------------------------------------------
        # Archived
        # --------------------------------------------------------------------

        if archived is not None:
            query = query.where(
                Collection.archived == archived,
            )

            count_query = count_query.where(
                Collection.archived == archived,
            )

        # --------------------------------------------------------------------
        # Total
        # --------------------------------------------------------------------

        total_result = await self.db.execute(
            count_query,
        )

        total = int(
            total_result.scalar_one() or 0,
        )

        # --------------------------------------------------------------------
        # Pagination
        # --------------------------------------------------------------------

        offset = (page - 1) * page_size

        query = (
            query
            .order_by(
                Collection.created_at.desc(),
                Collection.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(
            query,
        )

        collections = list(
            result.scalars().unique().all(),
        )

        # --------------------------------------------------------------------
        # Populate paper counts
        # --------------------------------------------------------------------

        if collections:
            collection_ids = [
                collection.id
                for collection in collections
            ]

            count_result = await self.db.execute(
                select(
                    CollectionItem.collection_id,
                    func.count(CollectionItem.id).label(
                        "paper_count",
                    ),
                )
                .where(
                    CollectionItem.collection_id.in_(
                        collection_ids,
                    ),
                )
                .group_by(
                    CollectionItem.collection_id,
                ),
            )

            paper_counts = {
                row.collection_id: int(row.paper_count)
                for row in count_result.all()
            }

            for collection in collections:
                collection.paper_count = paper_counts.get(
                    collection.id,
                    0,
                )

        return collections, total

    # ========================================================================
    # Get collection
    # ========================================================================

    async def get_collection(
        self,
        *,
        collection_id: int,
        user_id: int,
    ) -> Collection | None:
        """
        Return a collection belonging to the supplied user.

        Collection ID and owner ID are checked explicitly before
        loading the complete collection graph.
        """

        collection_id = int(collection_id)
        user_id = int(user_id)

        print(
            "[collections][repository] "
            f"GET collection_id={collection_id} "
            f"user_id={user_id}"
        )

        # --------------------------------------------------------------------
        # Check whether collection exists.
        # --------------------------------------------------------------------

        exists_result = await self.db.execute(
            select(
                Collection.id,
                Collection.user_id,
            )
            .where(
                Collection.id == collection_id,
            )
        )

        existing_row = exists_result.one_or_none()

        if existing_row is None:
            print(
                "[collections][repository] "
                f"COLLECTION DOES NOT EXIST "
                f"id={collection_id}"
            )

            return None

        existing_user_id = int(existing_row.user_id)

        print(
            "[collections][repository] "
            f"COLLECTION EXISTS "
            f"id={collection_id} "
            f"owner_user_id={existing_user_id} "
            f"requested_user_id={user_id}"
        )

        # --------------------------------------------------------------------
        # Ownership check
        # --------------------------------------------------------------------

        if existing_user_id != user_id:
            print(
                "[collections][repository] "
                f"OWNERSHIP MISMATCH "
                f"collection_id={collection_id} "
                f"owner_user_id={existing_user_id} "
                f"requested_user_id={user_id}"
            )

            return None

        # --------------------------------------------------------------------
        # Load complete collection graph
        # --------------------------------------------------------------------

        query = (
            select(Collection)
            .where(
                Collection.id == collection_id,
                Collection.user_id == user_id,
            )
            .options(
                *self._collection_load_options(),
            )
        )

        result = await self.db.execute(
            query,
        )

        collection = result.scalar_one_or_none()

        if collection is None:
            print(
                "[collections][repository] "
                f"COLLECTION DISAPPEARED AFTER OWNERSHIP CHECK "
                f"id={collection_id}"
            )

            return None

        # --------------------------------------------------------------------
        # Paper count
        # --------------------------------------------------------------------

        collection.paper_count = (
            await self.get_collection_item_count(
                collection_id=collection.id,
            )
        )

        print(
            "[collections][repository] "
            f"COLLECTION FOUND "
            f"id={collection.id} "
            f"user_id={collection.user_id} "
            f"paper_count={collection.paper_count}"
        )

        return collection

    # ========================================================================
    # Collection item count
    # ========================================================================

    async def get_collection_item_count(
        self,
        *,
        collection_id: int,
    ) -> int:
        """
        Return the number of papers in a collection.
        """

        result = await self.db.execute(
            select(
                func.count(CollectionItem.id),
            ).where(
                CollectionItem.collection_id == collection_id,
            ),
        )

        return int(
            result.scalar_one() or 0,
        )

    # ========================================================================
    # Create collection
    # ========================================================================

    async def create_collection(
        self,
        *,
        user_id: int,
        name: str,
        description: str | None = None,
        archived: bool = False,
    ) -> Collection:
        """
        Create a collection and return it with all response relationships
        eagerly loaded.
        """

        user_id = int(user_id)

        collection = Collection(
            user_id=user_id,
            name=name,
            description=description,
            archived=archived,
        )

        self.db.add(collection)

        await self.db.flush()

        collection_id = int(collection.id)

        print(
            "[collections][repository] "
            f"CREATED collection_id={collection_id} "
            f"user_id={user_id}"
        )

        # --------------------------------------------------------------------
        # Re-query with complete relationship graph.
        # --------------------------------------------------------------------

        query = (
            select(Collection)
            .where(
                Collection.id == collection_id,
                Collection.user_id == user_id,
            )
            .options(
                *self._collection_load_options(),
            )
        )

        result = await self.db.execute(
            query,
        )

        loaded_collection = result.scalar_one()

        loaded_collection.paper_count = 0

        print(
            "[collections][repository] "
            f"COLLECTION READY FOR RESPONSE "
            f"id={loaded_collection.id} "
            f"user_id={loaded_collection.user_id} "
            f"paper_count={loaded_collection.paper_count}"
        )

        return loaded_collection

    # ========================================================================
    # Update collection
    # ========================================================================

    async def update_collection(
        self,
        *,
        collection: Collection,
        data: dict[str, Any],
    ) -> Collection:
        """
        Update allowed collection fields.
        """

        allowed_fields = {
            "name",
            "description",
            "archived",
        }

        for key, value in data.items():
            if key in allowed_fields:
                setattr(
                    collection,
                    key,
                    value,
                )

        await self.db.flush()

        collection_id = int(collection.id)

        # --------------------------------------------------------------------
        # Re-query with complete relationship graph.
        # --------------------------------------------------------------------

        query = (
            select(Collection)
            .where(
                Collection.id == collection_id,
            )
            .options(
                *self._collection_load_options(),
            )
        )

        result = await self.db.execute(
            query,
        )

        loaded_collection = result.scalar_one()

        loaded_collection.paper_count = (
            await self.get_collection_item_count(
                collection_id=collection_id,
            )
        )

        return loaded_collection

    # ========================================================================
    # Delete collection
    # ========================================================================

    async def delete_collection(
        self,
        *,
        collection: Collection,
    ) -> None:
        """
        Delete a collection.
        """

        await self.db.delete(collection)

        await self.db.flush()

    # ========================================================================
    # Collection items
    # ========================================================================

    async def list_collection_items(
        self,
        *,
        collection_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CollectionItem], int]:
        """
        Return paginated collection items with their Paper graph eagerly
        loaded.
        """

        collection_id = int(collection_id)

        page = max(int(page), 1)
        page_size = max(int(page_size), 1)

        # --------------------------------------------------------------------
        # Count
        # --------------------------------------------------------------------

        count_result = await self.db.execute(
            select(
                func.count(CollectionItem.id),
            ).where(
                CollectionItem.collection_id == collection_id,
            ),
        )

        total = int(
            count_result.scalar_one() or 0,
        )

        # --------------------------------------------------------------------
        # Query
        # --------------------------------------------------------------------

        offset = (page - 1) * page_size

        query = (
            select(CollectionItem)
            .where(
                CollectionItem.collection_id == collection_id,
            )
            .options(
                *self._collection_item_load_options(),
            )
            .order_by(
                CollectionItem.created_at.desc(),
                CollectionItem.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(
            query,
        )

        items = list(
            result.scalars().unique().all(),
        )

        return items, total

    # ========================================================================
    # Get collection item
    # ========================================================================

    async def get_collection_item(
        self,
        *,
        collection_id: int,
        paper_id: int,
    ) -> CollectionItem | None:
        """
        Return a collection item if it exists.
        """

        collection_id = int(collection_id)
        paper_id = int(paper_id)

        query = (
            select(CollectionItem)
            .where(
                CollectionItem.collection_id == collection_id,
                CollectionItem.paper_id == paper_id,
            )
            .options(
                *self._collection_item_load_options(),
            )
        )

        result = await self.db.execute(
            query,
        )

        return result.scalar_one_or_none()

    # ========================================================================
    # Add collection item
    # ========================================================================

    async def add_collection_item(
        self,
        *,
        collection_id: int,
        paper_id: int,
    ) -> CollectionItem:
        """
        Add a paper to a collection.

        Duplicate entries are idempotent.
        """

        collection_id = int(collection_id)
        paper_id = int(paper_id)

        print(
            "[collections][repository] "
            f"ADD ITEM collection_id={collection_id} "
            f"paper_id={paper_id}"
        )

        # --------------------------------------------------------------------
        # Existing item
        # --------------------------------------------------------------------

        existing = await self.get_collection_item(
            collection_id=collection_id,
            paper_id=paper_id,
        )

        if existing is not None:
            print(
                "[collections][repository] "
                f"ITEM ALREADY EXISTS "
                f"collection_id={collection_id} "
                f"paper_id={paper_id}"
            )

            return existing

        # --------------------------------------------------------------------
        # Verify paper exists
        # --------------------------------------------------------------------

        paper_result = await self.db.execute(
            select(Paper.id).where(
                Paper.id == paper_id,
            )
        )

        if paper_result.scalar_one_or_none() is None:
            raise ValueError(
                f"Paper {paper_id} does not exist.",
            )

        # --------------------------------------------------------------------
        # Verify collection exists
        # --------------------------------------------------------------------

        collection_result = await self.db.execute(
            select(Collection.id).where(
                Collection.id == collection_id,
            )
        )

        if collection_result.scalar_one_or_none() is None:
            raise ValueError(
                f"Collection {collection_id} does not exist.",
            )

        # --------------------------------------------------------------------
        # Create item
        # --------------------------------------------------------------------

        item = CollectionItem(
            collection_id=collection_id,
            paper_id=paper_id,
        )

        self.db.add(item)

        await self.db.flush()

        # --------------------------------------------------------------------
        # Re-query with all required relationships.
        # --------------------------------------------------------------------

        query = (
            select(CollectionItem)
            .where(
                CollectionItem.id == item.id,
            )
            .options(
                *self._collection_item_load_options(),
            )
        )

        result = await self.db.execute(
            query,
        )

        loaded_item = result.scalar_one()

        print(
            "[collections][repository] "
            f"ITEM CREATED id={loaded_item.id} "
            f"collection_id={loaded_item.collection_id} "
            f"paper_id={loaded_item.paper_id}"
        )

        return loaded_item

    # ========================================================================
    # Remove collection item
    # ========================================================================

    async def remove_collection_item(
        self,
        *,
        collection_id: int,
        paper_id: int,
    ) -> bool:
        """
        Remove a paper from a collection.

        Returns:
            True  -> item deleted
            False -> item did not exist
        """

        collection_id = int(collection_id)
        paper_id = int(paper_id)

        item = await self.get_collection_item(
            collection_id=collection_id,
            paper_id=paper_id,
        )

        if item is None:
            return False

        await self.db.delete(item)

        await self.db.flush()

        return True