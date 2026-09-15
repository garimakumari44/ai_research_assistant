from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import select

from app.indexing.embeddings.generator import EmbeddingGenerator
from app.indexing.vector_store.persistence import FAISSPersistence
from app.knowledge.indexing.vector import (
    VectorIndexItem,
    VectorIndexer,
)
from app.workers.celery_app import celery_app


logger = logging.getLogger(__name__)


VECTOR_DIMENSION = 384


def _run(coro: Any) -> Any:
    """
    Run an async operation from a Celery task.
    """

    return asyncio.run(coro)


# ======================================================================
# DATABASE / METADATA HELPERS
# ======================================================================


async def _load_chunk_with_paper(
    *,
    chunk_id: UUID,
) -> tuple[Any, Any, Any]:
    """
    Load one chunk together with its parent document and paper.

    The database relationship is:

        Chunk
          |
          +-- document_id
                |
                v
             Document
                |
                +-- paper_id
                      |
                      v
                    Paper

    Document.paper is not defined as an ORM relationship, so this
    function deliberately uses explicit SQL joins.
    """

    from app.db.models.chunk import Chunk
    from app.db.models.document import Document
    from app.db.models.paper import Paper
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Chunk,
                Document,
                Paper,
            )
            .join(
                Document,
                Chunk.document_id == Document.id,
            )
            .outerjoin(
                Paper,
                Document.paper_id == Paper.id,
            )
            .where(
                Chunk.id == chunk_id,
            )
        )

        row = result.one_or_none()

        if row is None:
            return None, None, None

        chunk, document, paper = row

        return (
            chunk,
            document,
            paper,
        )


async def _load_chunks_for_document(
    *,
    document_id: UUID,
) -> list[tuple[Any, Any, Any]]:
    """
    Load all chunks belonging to a document together with their
    parent document and paper.

    Returns:

        [
            (chunk, document, paper),
            ...
        ]

    Explicit joins are used because Document.paper is not defined
    as an ORM relationship.
    """

    from app.db.models.chunk import Chunk
    from app.db.models.document import Document
    from app.db.models.paper import Paper
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Chunk,
                Document,
                Paper,
            )
            .join(
                Document,
                Chunk.document_id == Document.id,
            )
            .outerjoin(
                Paper,
                Document.paper_id == Paper.id,
            )
            .where(
                Chunk.document_id == document_id,
            )
            .order_by(
                Chunk.chunk_index,
            )
        )

        return list(
            result.all()
        )


# ======================================================================
# PERSISTED INDEX HELPERS
# ======================================================================


def _load_existing_vector_items(
    persistence: FAISSPersistence,
) -> list[VectorIndexItem]:
    """
    Load the existing persisted vector state.

    FAISSPersistence stores:
        - FAISS index
        - chunk IDs
        - vectors

    It intentionally does not store metadata.

    Therefore existing vector metadata is restored as empty here.
    When a chunk is subsequently indexed, its canonical PostgreSQL
    metadata is attached through _build_chunk_metadata().

    New/upserted chunks replace the existing metadata for those IDs.
    """

    persisted = persistence.load()

    if persisted is None:
        return []

    persisted_ids = persisted["ids"]
    persisted_vectors = persisted.get(
        "vectors"
    )

    if persisted_vectors is None:
        raise RuntimeError(
            "Persistent FAISS index exists but vectors.npy is missing. "
            "The vector index cannot be safely merged."
        )

    vectors = np.asarray(
        persisted_vectors,
        dtype=np.float32,
    )

    if vectors.ndim != 2:
        raise RuntimeError(
            "Persisted vectors must be a 2-dimensional array."
        )

    if vectors.shape[1] != VECTOR_DIMENSION:
        raise RuntimeError(
            "Persisted vector dimension mismatch: "
            f"expected {VECTOR_DIMENSION}, "
            f"received {vectors.shape[1]}."
        )

    if len(persisted_ids) != len(vectors):
        raise RuntimeError(
            "Persistent vector index is inconsistent: "
            f"{len(persisted_ids)} IDs vs "
            f"{len(vectors)} vectors."
        )

    items: list[VectorIndexItem] = []

    for chunk_id_string, vector in zip(
        persisted_ids,
        vectors,
        strict=True,
    ):
        try:
            chunk_uuid = UUID(
                str(chunk_id_string)
            )
        except (
            ValueError,
            TypeError,
        ) as exc:
            raise RuntimeError(
                "Invalid chunk ID in persistent vector index: "
                f"{chunk_id_string}"
            ) from exc

        items.append(
            VectorIndexItem(
                chunk_id=chunk_uuid,
                vector=vector.tolist(),
                metadata={},
            )
        )

    return items


def _build_chunk_metadata(
    chunk: Any,
    document: Any = None,
    paper: Any = None,
) -> dict[str, Any]:
    """
    Build application-level metadata for a chunk.

    The canonical metadata hierarchy is:

        Chunk
          |
          +-- Document
                |
                +-- Paper

    The document and paper objects are supplied explicitly by the
    database loader. This avoids asynchronous SQLAlchemy lazy-loading.

    The function also accepts None for document/paper so it remains
    safe for callers that only have a Chunk object.
    """

    metadata: dict[str, Any] = {
        "chunk_id": str(
            chunk.id
        ),
        "document_id": str(
            chunk.document_id
        ),
        "section_id": str(
            chunk.section_id
        ),
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "token_count": chunk.token_count,
    }

    # ------------------------------------------------------------------
    # EXISTING CHUNK METADATA
    # ------------------------------------------------------------------

    chunk_metadata = getattr(
        chunk,
        "metadata_",
        None,
    )

    if isinstance(
        chunk_metadata,
        dict,
    ):
        metadata.update(
            dict(chunk_metadata)
        )

    # Reassert canonical identifiers after merging stored metadata.
    metadata["chunk_id"] = str(
        chunk.id
    )

    metadata["document_id"] = str(
        chunk.document_id
    )

    metadata["section_id"] = str(
        chunk.section_id
    )

    metadata["chunk_index"] = chunk.chunk_index
    metadata["page_number"] = chunk.page_number
    metadata["token_count"] = chunk.token_count

    # ------------------------------------------------------------------
    # DOCUMENT METADATA
    # ------------------------------------------------------------------

    if document is not None:
        document_name = getattr(
            document,
            "name",
            None,
        )

        if document_name:
            document_name = str(
                document_name
            ).strip()

            if document_name:
                metadata["document_name"] = document_name

        document_type = getattr(
            document,
            "document_type",
            None,
        )

        if document_type:
            document_type = str(
                document_type
            ).strip()

            if document_type:
                metadata["document_type"] = document_type

        document_description = getattr(
            document,
            "description",
            None,
        )

        if document_description:
            document_description = str(
                document_description
            ).strip()

            if document_description:
                metadata["document_description"] = (
                    document_description
                )

        document_paper_id = getattr(
            document,
            "paper_id",
            None,
        )

        if document_paper_id is not None:
            metadata["paper_id"] = str(
                document_paper_id
            )

    # ------------------------------------------------------------------
    # PAPER METADATA
    # ------------------------------------------------------------------

    if paper is not None:
        paper_id = getattr(
            paper,
            "id",
            None,
        )

        if paper_id is not None:
            metadata["paper_id"] = str(
                paper_id
            )

        title = getattr(
            paper,
            "title",
            None,
        )

        if title:
            title = str(
                title
            ).strip()

            if title:
                metadata["title"] = title

        abstract = getattr(
            paper,
            "abstract",
            None,
        )

        if abstract:
            abstract = str(
                abstract
            ).strip()

            if abstract:
                metadata["paper_abstract"] = abstract

        year = getattr(
            paper,
            "year",
            None,
        )

        if year is not None:
            metadata["year"] = year

        arxiv_id = getattr(
            paper,
            "arxiv_id",
            None,
        )

        if arxiv_id:
            arxiv_id = str(
                arxiv_id
            ).strip()

            if arxiv_id:
                metadata["arxiv_id"] = arxiv_id

        doi = getattr(
            paper,
            "doi",
            None,
        )

        if doi:
            doi = str(
                doi
            ).strip()

            if doi:
                metadata["doi"] = doi

        landing_page_url = getattr(
            paper,
            "landing_page_url",
            None,
        )

        if landing_page_url:
            landing_page_url = str(
                landing_page_url
            ).strip()

            if landing_page_url:
                metadata["landing_page_url"] = (
                    landing_page_url
                )

        pdf_url = getattr(
            paper,
            "pdf_url",
            None,
        )

        if pdf_url:
            pdf_url = str(
                pdf_url
            ).strip()

            if pdf_url:
                metadata["pdf_url"] = pdf_url

        provider = getattr(
            paper,
            "provider",
            None,
        )

        if provider:
            provider = str(
                provider
            ).strip()

            if provider:
                metadata["provider"] = provider

        provider_paper_id = getattr(
            paper,
            "provider_paper_id",
            None,
        )

        if provider_paper_id:
            provider_paper_id = str(
                provider_paper_id
            ).strip()

            if provider_paper_id:
                metadata["provider_paper_id"] = (
                    provider_paper_id
                )

    return metadata


def _validate_embedding(
    embedding: Any,
    *,
    chunk_id: UUID,
) -> np.ndarray:
    """
    Validate one generated embedding.
    """

    vector = np.asarray(
        embedding,
        dtype=np.float32,
    )

    if vector.ndim != 1:
        vector = vector.reshape(-1)

    if vector.size != VECTOR_DIMENSION:
        raise RuntimeError(
            "Embedding dimension mismatch for chunk "
            f"{chunk_id}: expected {VECTOR_DIMENSION}, "
            f"received {vector.size}."
        )

    if not np.all(
        np.isfinite(vector)
    ):
        raise RuntimeError(
            f"Embedding contains non-finite values for chunk {chunk_id}."
        )

    return np.ascontiguousarray(
        vector,
        dtype=np.float32,
    )


def _persist_vector_index(
    persistence: FAISSPersistence,
    vector_indexer: VectorIndexer,
) -> int:
    """
    Persist the complete authoritative VectorIndexer state.

    Metadata remains in application memory and is reconstructed from
    PostgreSQL when the FastAPI application starts.
    """

    final_items = vector_indexer.items()

    if not final_items:
        raise RuntimeError(
            "Vector index is empty after indexing."
        )

    final_ids = [
        str(item.chunk_id)
        for item in final_items
    ]

    final_vectors = np.asarray(
        [
            item.vector
            for item in final_items
        ],
        dtype=np.float32,
    )

    if final_vectors.ndim != 2:
        raise RuntimeError(
            "Final vector matrix must be 2-dimensional."
        )

    if final_vectors.shape[0] != len(
        final_ids
    ):
        raise RuntimeError(
            "Final vector/ID count mismatch: "
            f"{final_vectors.shape[0]} vectors vs "
            f"{len(final_ids)} IDs."
        )

    if final_vectors.shape[1] != VECTOR_DIMENSION:
        raise RuntimeError(
            "Final vector dimension mismatch: "
            f"expected {VECTOR_DIMENSION}, "
            f"received {final_vectors.shape[1]}."
        )

    persistence.save(
        vector_indexer.faiss.index,
        final_ids,
        final_vectors,
    )

    return len(
        final_items
    )


# ======================================================================
# DOCUMENT INDEXING
# ======================================================================


@celery_app.task(
    bind=True,
    name="app.workers.tasks.indexing.index_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def index_document(
    self,
    document_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """
    Generate embeddings for every chunk in a document and merge them
    into the persistent FAISS vector index.
    """

    logger.info(
        "Starting document indexing",
        extra={
            "document_id": document_id,
            "force": force,
            "task_id": self.request.id,
        },
    )

    try:
        document_uuid = UUID(
            document_id
        )
    except (
        ValueError,
        TypeError,
    ) as exc:
        raise ValueError(
            f"Invalid document_id: {document_id}"
        ) from exc

    result = _run(
        _index_document(
            document_id=document_uuid,
            force=force,
        )
    )

    logger.info(
        "Document indexing completed",
        extra={
            "document_id": document_id,
            "task_id": self.request.id,
            "chunks_found": result.get(
                "chunks_found",
                0,
            ),
            "chunks_indexed": result.get(
                "chunks_indexed",
                0,
            ),
        },
    )

    return {
        "status": "completed",
        "document_id": document_id,
        "result": result,
    }


async def _index_document(
    *,
    document_id: UUID,
    force: bool,
) -> dict[str, Any]:
    """
    Load chunks from PostgreSQL, explicitly load their parent document
    and paper, generate embeddings, merge them into the existing
    persistent vector index, and save the result.
    """

    rows = await _load_chunks_for_document(
        document_id=document_id
    )

    chunks = [
        chunk
        for chunk, _, _ in rows
    ]

    if not chunks:
        logger.warning(
            "No chunks found for document %s",
            document_id,
        )

        return {
            "chunks_found": 0,
            "chunks_indexed": 0,
            "total_vectors": 0,
            "force": force,
        }

    persistence = FAISSPersistence()

    existing_items = _load_existing_vector_items(
        persistence
    )

    vector_indexer = VectorIndexer(
        dimension=VECTOR_DIMENSION,
    )

    if existing_items:
        vector_indexer.restore_items(
            existing_items
        )

    # ------------------------------------------------------------------
    # EMBEDDINGS
    # ------------------------------------------------------------------

    generator = EmbeddingGenerator(
        model_name=EmbeddingGenerator.DEFAULT_MODEL,
        device=EmbeddingGenerator.DEFAULT_DEVICE,
        batch_size=EmbeddingGenerator.DEFAULT_BATCH_SIZE,
    )

    if generator.dimension != VECTOR_DIMENSION:
        raise RuntimeError(
            "Embedding model dimension does not match "
            "the vector index: "
            f"expected {VECTOR_DIMENSION}, "
            f"received {generator.dimension}."
        )

    texts = [
        chunk.content
        for chunk, _, _ in rows
    ]

    embeddings = generator.embed_texts(
        texts
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count mismatch: "
            f"expected {len(chunks)}, "
            f"received {len(embeddings)}."
        )

    new_items: list[VectorIndexItem] = []

    for (
        chunk,
        document,
        paper,
    ), embedding in zip(
        rows,
        embeddings,
        strict=True,
    ):
        vector = _validate_embedding(
            embedding,
            chunk_id=chunk.id,
        )

        metadata = _build_chunk_metadata(
            chunk=chunk,
            document=document,
            paper=paper,
        )

        new_items.append(
            VectorIndexItem(
                chunk_id=chunk.id,
                vector=vector.tolist(),
                metadata=metadata,
            )
        )

    # ------------------------------------------------------------------
    # MERGE
    # ------------------------------------------------------------------

    await vector_indexer.upsert_many(
        new_items
    )

    # ------------------------------------------------------------------
    # PERSIST COMPLETE INDEX
    # ------------------------------------------------------------------

    total_vectors = _persist_vector_index(
        persistence,
        vector_indexer,
    )

    logger.info(
        "Persistent vector index updated",
        extra={
            "document_id": str(
                document_id
            ),
            "document_chunks": len(chunks),
            "new_vectors": len(new_items),
            "total_vectors": total_vectors,
        },
    )

    return {
        "chunks_found": len(chunks),
        "chunks_indexed": len(new_items),
        "total_vectors": total_vectors,
        "force": force,
    }


# ======================================================================
# SINGLE CHUNK INDEXING
# ======================================================================


@celery_app.task(
    bind=True,
    name="app.workers.tasks.indexing.index_chunk",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
)
def index_chunk(
    self,
    chunk_id: str,
) -> dict[str, Any]:
    """
    Generate an embedding for one chunk and merge it into the
    persistent vector index.
    """

    try:
        chunk_uuid = UUID(
            chunk_id
        )
    except (
        ValueError,
        TypeError,
    ) as exc:
        raise ValueError(
            f"Invalid chunk_id: {chunk_id}"
        ) from exc

    result = _run(
        _index_chunk(
            chunk_id=chunk_uuid
        )
    )

    return {
        "status": "completed",
        "chunk_id": chunk_id,
        "result": result,
    }


async def _index_chunk(
    *,
    chunk_id: UUID,
) -> dict[str, Any]:
    """
    Index one chunk into the persistent vector index.

    The parent document and paper are explicitly loaded using SQL
    joins so that canonical paper metadata can be attached without
    asynchronous SQLAlchemy lazy-loading.
    """

    chunk, document, paper = await _load_chunk_with_paper(
        chunk_id=chunk_id
    )

    if chunk is None:
        raise ValueError(
            f"Chunk not found: {chunk_id}"
        )

    # ------------------------------------------------------------------
    # EMBEDDING
    # ------------------------------------------------------------------

    generator = EmbeddingGenerator(
        model_name=EmbeddingGenerator.DEFAULT_MODEL,
        device=EmbeddingGenerator.DEFAULT_DEVICE,
        batch_size=EmbeddingGenerator.DEFAULT_BATCH_SIZE,
    )

    if generator.dimension != VECTOR_DIMENSION:
        raise RuntimeError(
            "Embedding model dimension does not match "
            "the vector index: "
            f"expected {VECTOR_DIMENSION}, "
            f"received {generator.dimension}."
        )

    embedding = generator.embed_text(
        chunk.content
    )

    vector = _validate_embedding(
        embedding,
        chunk_id=chunk_id,
    )

    metadata = _build_chunk_metadata(
        chunk=chunk,
        document=document,
        paper=paper,
    )

    new_item = VectorIndexItem(
        chunk_id=chunk.id,
        vector=vector.tolist(),
        metadata=metadata,
    )

    # ------------------------------------------------------------------
    # LOAD EXISTING INDEX
    # ------------------------------------------------------------------

    persistence = FAISSPersistence()

    existing_items = _load_existing_vector_items(
        persistence
    )

    vector_indexer = VectorIndexer(
        dimension=VECTOR_DIMENSION
    )

    if existing_items:
        vector_indexer.restore_items(
            existing_items
        )

    # ------------------------------------------------------------------
    # UPSERT SINGLE CHUNK
    # ------------------------------------------------------------------

    await vector_indexer.upsert(
        chunk_id=new_item.chunk_id,
        vector=new_item.vector,
        metadata=new_item.metadata,
    )

    # ------------------------------------------------------------------
    # PERSIST COMPLETE INDEX
    # ------------------------------------------------------------------

    total_vectors = _persist_vector_index(
        persistence,
        vector_indexer,
    )

    logger.info(
        "Chunk indexed successfully",
        extra={
            "chunk_id": str(
                chunk_id
            ),
            "total_vectors": total_vectors,
        },
    )

    return {
        "chunk_id": str(
            chunk_id
        ),
        "indexed": True,
        "total_vectors": total_vectors,
    }


__all__ = [
    "index_document",
    "index_chunk",
]