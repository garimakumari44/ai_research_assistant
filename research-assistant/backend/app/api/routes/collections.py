from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUserId
from app.db.session import get_db
from app.schemas.collections import (
    CollectionCreate,
    CollectionItemCreate,
    CollectionItemListResponse,
    CollectionItemResponse,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
)
from app.services.collection_service import CollectionService


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)


# ============================================================================
# Dependencies
# ============================================================================


def get_collection_service(
    db: AsyncSession = Depends(get_db),
) -> CollectionService:
    """
    Create a CollectionService using the request-scoped database session.
    """

    return CollectionService(db)


# ============================================================================
# Collection CRUD
# ============================================================================


@router.get(
    "",
    response_model=CollectionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_collections(
    page: int = Query(
        1,
        ge=1,
        description="Page number.",
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of collections per page.",
    ),
    search: str | None = Query(
        None,
        description="Optional collection name search.",
    ),
    archived: bool | None = Query(
        None,
        description="Filter by archived status.",
    ),
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Return a paginated list of collections belonging to the
    authenticated user.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    # TEMPORARY DIAGNOSTIC LOGGING
    print(
        f"[collections] LIST "
        f"user_id={current_user_id} "
        f"page={page} "
        f"page_size={page_size} "
        f"search={search!r} "
        f"archived={archived}"
    )

    try:
        return await service.list_collections(
            user_id=current_user_id,
            page=page,
            page_size=page_size,
            search=search,
            archived=archived,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


# ============================================================================


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    payload: CollectionCreate,
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Create a new collection.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        return await service.create_collection(
            user_id=current_user_id,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================================


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_collection(
    collection_id: int,
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Return a single collection belonging to the authenticated user.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    # TEMPORARY DIAGNOSTIC LOGGING
    print(
        f"[collections] GET DETAIL "
        f"collection_id={collection_id} "
        f"user_id={current_user_id}"
    )

    try:
        collection = await service.get_collection(
            user_id=current_user_id,
            collection_id=collection_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return collection


# ============================================================================


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_collection(
    collection_id: int,
    payload: CollectionUpdate,
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Update an existing collection.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        collection = await service.update_collection(
            user_id=current_user_id,
            collection_id=collection_id,
            payload=payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return collection


# ============================================================================


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_collection(
    collection_id: int,
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Delete a collection.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        deleted = await service.delete_collection(
            user_id=current_user_id,
            collection_id=collection_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return None


# ============================================================================
# Collection Items
# ============================================================================


@router.get(
    "/{collection_id}/items",
    response_model=CollectionItemListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_collection_items(
    collection_id: int,
    page: int = Query(
        1,
        ge=1,
        description="Page number.",
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of items per page.",
    ),
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Return papers/items belonging to a collection.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        result = await service.list_collection_items(
            user_id=current_user_id,
            collection_id=collection_id,
            page=page,
            page_size=page_size,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return result


# ============================================================================


@router.post(
    "/{collection_id}/items",
    response_model=CollectionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_collection_item(
    collection_id: int,
    payload: CollectionItemCreate,
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Add a paper to a collection.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        item = await service.add_collection_item(
            user_id=current_user_id,
            collection_id=collection_id,
            paper_id=payload.paper_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return item


# ============================================================================


@router.delete(
    "/{collection_id}/items/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_collection_item(
    collection_id: int,
    paper_id: int,
    service: CollectionService = Depends(
        get_collection_service
    ),
    current_user_id: CurrentUserId = None,
):
    """
    Remove a paper from a collection.
    """

    if current_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        removed = await service.remove_collection_item(
            user_id=current_user_id,
            collection_id=collection_id,
            paper_id=paper_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection item not found.",
        )

    return None