from __future__ import annotations

from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.models.paper import Paper
from app.db.session import AsyncSessionLocal
from app.indexing.vector_store.persistence import FAISSPersistence
from app.knowledge.indexing.keyword import KeywordIndexItem
from app.knowledge.indexing.manager import IndexManager
from app.knowledge.indexing.registry import IndexRegistry
from app.knowledge.indexing.vector import VectorIndexItem


# ============================================================================
# CONSTANTS
# ============================================================================

VECTOR_DIMENSION = 384


# ============================================================================
# CORS
# ============================================================================

def _build_cors_origins() -> list[str]:
    """
    Build the allowed CORS origins.

    Local development must support both:
        http://localhost:3000
        http://127.0.0.1:3000

    Additional origins configured through application settings are preserved.
    """

    origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    try:
        configured_origins = settings.cors_origins_list
    except Exception:
        configured_origins = []

    for origin in configured_origins:
        normalized = str(origin).strip().rstrip("/")

        if normalized and normalized not in origins:
            origins.append(normalized)

    return origins


# ============================================================================
# LOAD CHUNKS FROM DATABASE
# ============================================================================

async def _load_chunks() -> list[Chunk]:
    """
    Load all chunks from PostgreSQL.

    PostgreSQL is authoritative for chunk and paper metadata.
    """

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Chunk,
                Document.paper_id,
                Paper.title,
                Paper.abstract,
            )
            .join(
                Document,
                Chunk.document_id == Document.id,
            )
            .outerjoin(
                Paper,
                Document.paper_id == Paper.id,
            )
        )

        chunks: list[Chunk] = []

        for (
            chunk,
            paper_id,
            paper_title,
            paper_abstract,
        ) in result.all():

            metadata = dict(
                chunk.metadata_ or {}
            )

            if paper_id is not None:
                metadata["paper_id"] = str(paper_id)

            if paper_title:
                title = str(paper_title).strip()

                if title:
                    metadata["title"] = title

            if paper_abstract:
                abstract = str(paper_abstract).strip()

                if abstract:
                    metadata["paper_abstract"] = abstract

            chunk.metadata_ = metadata

            chunks.append(chunk)

        return chunks


# ============================================================================
# BUILD KEYWORD INDEX
# ============================================================================

async def _restore_keyword_index(
    index_registry: IndexRegistry,
    chunks: list[Chunk],
) -> int:
    """
    Rebuild the keyword/BM25 index from PostgreSQL.
    """

    keyword_items: list[KeywordIndexItem] = []

    for chunk in chunks:
        keyword_items.append(
            KeywordIndexItem(
                chunk_id=chunk.id,
                text=chunk.content,
                metadata={
                    **dict(chunk.metadata_ or {}),
                    "document_id": str(chunk.document_id),
                    "section_id": str(chunk.section_id),
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "token_count": chunk.token_count,
                },
            )
        )

    if keyword_items:
        await index_registry.keyword.upsert_many(
            keyword_items
        )

    return len(keyword_items)


# ============================================================================
# RESTORE PERSISTED VECTOR INDEX
# ============================================================================

async def _restore_persisted_vector_index(
    index_registry: IndexRegistry,
    chunks: list[Chunk],
) -> int:
    """
    Restore the persisted FAISS/vector index.

    FAISS is authoritative for embeddings.
    PostgreSQL is authoritative for metadata.
    """

    persistence = FAISSPersistence()

    persisted = persistence.load()

    if persisted is None:
        print(
            "Persisted FAISS index not found."
        )
        print(
            "Vector index will remain empty until "
            "the indexing pipeline creates/persists embeddings."
        )

        return 0

    persisted_ids = persisted.get(
        "ids",
        [],
    )

    persisted_vectors = persisted.get(
        "vectors"
    )

    if persisted_vectors is None:
        raise RuntimeError(
            "Persistent FAISS index exists but "
            "vectors.npy is missing."
        )

    vectors = np.asarray(
        persisted_vectors,
        dtype=np.float32,
    )

    if vectors.size == 0:
        print(
            "Persisted vector index contains zero vectors."
        )

        index_registry.vector.restore_items([])

        return 0

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

    persisted_index = persisted.get("index")

    if persisted_index is None:
        raise RuntimeError(
            "Persisted FAISS state does not contain an index."
        )

    if int(persisted_index.ntotal) != len(persisted_ids):
        raise RuntimeError(
            "Persistent FAISS index is inconsistent: "
            f"FAISS contains {persisted_index.ntotal} vectors but "
            f"ids.json contains {len(persisted_ids)} IDs."
        )

    if int(persisted_index.d) != VECTOR_DIMENSION:
        raise RuntimeError(
            "Persisted FAISS index dimension mismatch: "
            f"expected {VECTOR_DIMENSION}, "
            f"received {persisted_index.d}."
        )

    chunks_by_id = {
        str(chunk.id): chunk
        for chunk in chunks
    }

    vector_items: list[VectorIndexItem] = []
    missing_chunks: list[str] = []

    for chunk_id_string, vector in zip(
        persisted_ids,
        vectors,
        strict=True,
    ):
        normalized_chunk_id = str(
            chunk_id_string
        )

        chunk = chunks_by_id.get(
            normalized_chunk_id
        )

        if chunk is None:
            missing_chunks.append(
                normalized_chunk_id
            )
            continue

        vector_items.append(
            VectorIndexItem(
                chunk_id=chunk.id,
                vector=vector.tolist(),
                metadata={
                    **dict(chunk.metadata_ or {}),
                    "document_id": str(chunk.document_id),
                    "section_id": str(chunk.section_id),
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "token_count": chunk.token_count,
                },
            )
        )

    index_registry.vector.restore_items(
        vector_items
    )

    restored_count = await index_registry.vector.count()

    if restored_count != len(vector_items):
        raise RuntimeError(
            "Vector index restoration count mismatch: "
            f"expected {len(vector_items)}, "
            f"received {restored_count}."
        )

    print(
        "Persisted FAISS index restored: "
        f"{restored_count} vectors."
    )

    if missing_chunks:
        print(
            "Warning: "
            f"{len(missing_chunks)} persisted vector IDs "
            "were not found in PostgreSQL and were skipped."
        )

    return restored_count


# ============================================================================
# RESTORE ALL INDEXES
# ============================================================================

async def _load_persisted_indexes(
    index_registry: IndexRegistry,
) -> None:
    """
    Restore keyword and vector indexes.
    """

    print(
        "Restoring retrieval indexes..."
    )

    chunks = await _load_chunks()

    print(
        f"Loaded {len(chunks)} chunks from PostgreSQL."
    )

    keyword_count = await _restore_keyword_index(
        index_registry=index_registry,
        chunks=chunks,
    )

    print(
        f"Keyword index restored: {keyword_count} items."
    )

    vector_count = await _restore_persisted_vector_index(
        index_registry=index_registry,
        chunks=chunks,
    )

    stats = await index_registry.get_stats()

    print(
        "Index restoration completed: "
        f"vectors={vector_count}, "
        f"keywords={keyword_count}."
    )

    print(
        "Index registry statistics: "
        f"{stats}"
    )

    if vector_count == 0 and len(chunks) > 0:
        print(
            "WARNING: PostgreSQL contains chunks but the "
            "vector index contains zero vectors."
        )

        print(
            "Semantic/hybrid retrieval may return zero sources "
            "until the embedding/indexing pipeline populates FAISS."
        )


# ============================================================================
# APPLICATION LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """

    print(
        f"Starting {settings.APP_NAME} "
        f"v{settings.APP_VERSION}..."
    )

    print(
        f"Environment: {settings.ENVIRONMENT}"
    )

    index_registry = IndexRegistry.create()

    print(
        "IndexRegistry initialized."
    )

    index_manager = IndexManager(
        index_registry=index_registry,
    )

    print(
        "IndexManager initialized."
    )

    app.state.index_registry = index_registry
    app.state.index_manager = index_manager

    # ------------------------------------------------------------------------
    # INDEX RESTORATION
    # ------------------------------------------------------------------------

    try:
        await _load_persisted_indexes(
            index_registry
        )

        print(
            "Application startup completed."
        )

    except Exception as exc:
        # IMPORTANT:
        #
        # Retrieval-index restoration must NOT prevent FastAPI itself
        # from starting. PostgreSQL remains available and the indexing
        # pipeline can rebuild the indexes later.
        #
        # This is particularly important during development because
        # an index corruption/mismatch should not produce a browser
        # "Failed to fetch" error for the entire API.

        print(
            "WARNING: retrieval index restoration failed: "
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "FastAPI will continue starting with the available "
            "in-memory indexes."
        )

    try:
        yield

    finally:
        try:
            stats = await index_registry.get_stats()

            print(
                "Index registry before shutdown: "
                f"{stats}"
            )

        except Exception as exc:
            print(
                "Warning: unable to read index statistics "
                f"during shutdown: {exc}"
            )

        try:
            await index_registry.clear()

            print(
                "IndexRegistry cleared."
            )

        except Exception as exc:
            print(
                "Warning: failed to clear IndexRegistry: "
                f"{exc}"
            )

        print(
            f"Shutting down {settings.APP_NAME}..."
        )


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# ============================================================================
# APPLICATION EXCEPTION HANDLER
# ============================================================================

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


# ============================================================================
# CORS
# ============================================================================

CORS_ORIGINS = _build_cors_origins()

print(
    "CORS origins:",
    CORS_ORIGINS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ROUTES
# ============================================================================

app.include_router(
    api_router
)


# ============================================================================
# ROOT
# ============================================================================

@app.get(
    "/",
    tags=["System"],
)
async def root() -> dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get(
    "/health",
    tags=["System"],
)
async def health() -> dict[str, str]:
    """
    Basic health check.

    Keep this endpoint independent of:
        - authentication
        - research
        - retrieval
        - FAISS
        - LLM
    """

    return {
        "status": "healthy",
    }