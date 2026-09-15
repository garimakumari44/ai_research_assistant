
from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================================
# RESPONSE CONVERSION
# ============================================================================


def _document_to_response(document) -> DocumentResponse:
    """
    Convert the SQLAlchemy Document model into the public API response.

    Database model:
        document.name

    API contract:
        DocumentResponse.filename

    We intentionally map `name` -> `filename` here instead of changing
    the database model/schema.
    """

    return DocumentResponse.model_validate(
        {
            "id": document.id,
            "filename": document.name,
            "description": document.description,
            "document_type": document.document_type,
            "status": document.status,
            "paper_id": document.paper_id,
            "metadata": document.metadata,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
    )


# ============================================================================
# POST /documents
# ============================================================================


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
)
async def create_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Create a document record from an uploaded file.

    Current responsibility:
        - Validate the uploaded file.
        - Create the document metadata record.

    Actual document downloading, extraction, parsing, storage,
    chunking, embedding, and indexing belong to the Phase 2
    document ingestion pipeline.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    filename = file.filename.strip()

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid filename is required.",
        )

    repository = DocumentRepository(db)

    document = await repository.create_document(
        filename=filename,
        content_type=file.content_type,
    )

    return _document_to_response(document)


# ============================================================================
# GET /documents
# ============================================================================


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
)
async def list_documents(
    paper_id: int | None = Query(
        default=None,
        description="Filter documents by paper ID.",
    ),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """
    Return documents.

    If `paper_id` is supplied, only documents belonging to that
    paper are returned.

    Examples:
        GET /api/v1/documents
        GET /api/v1/documents?paper_id=7
    """

    repository = DocumentRepository(db)

    documents = await repository.list_documents(
        paper_id=paper_id,
    )

    return DocumentListResponse(
        items=[
            _document_to_response(document)
            for document in documents
        ],
        total=len(documents),
    )


# ============================================================================
# GET /documents/{document_id}
# ============================================================================


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Return a single document by ID.
    """

    repository = DocumentRepository(db)

    document = await repository.get_document(
        document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return _document_to_response(document)


# ============================================================================
# DELETE /documents/{document_id}
# ============================================================================


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a document by ID.
    """

    repository = DocumentRepository(db)

    deleted = await repository.delete_document(
        document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return None

