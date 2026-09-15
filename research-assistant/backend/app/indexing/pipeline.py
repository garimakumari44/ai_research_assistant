from __future__ import annotations

from typing import Any, Dict, List

from app.core.logging import logger
from app.indexing.embeddings.generator import EmbeddingGenerator
from app.indexing.metadata.schema import ChunkMetadata
from app.indexing.metadata.store import MetadataStore
from app.indexing.vector_store.faiss_index import FAISSIndex
from app.indexing.vector_store.persistence import FAISSPersistence


class IndexingPipeline:
    """
    Concrete indexing pipeline.

    Flow:

        PostgreSQL chunks
              |
              v
        EmbeddingGenerator
              |
              v
        FAISSIndex
              |
              +----> MetadataStore
              |
              v
        FAISSPersistence

    The PostgreSQL document_chunks table remains the source of truth
    for chunk content and relationships.
    """

    def __init__(
        self,
        *,
        embedding_generator: EmbeddingGenerator | None = None,
        vector_index: FAISSIndex | None = None,
        persistence: FAISSPersistence | None = None,
        metadata_store: MetadataStore | None = None,
    ) -> None:
        self.embedding_generator = (
            embedding_generator
            or EmbeddingGenerator()
        )

        self.vector_index = (
            vector_index
            or FAISSIndex()
        )

        self.persistence = (
            persistence
            or FAISSPersistence()
        )

        self.metadata_store = (
            metadata_store
            or MetadataStore()
        )

    def index(
        self,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Index a collection of chunks.

        Expected input:

            [
                {
                    "id": "...",
                    "document_id": "...",
                    "section_id": "...",
                    "text": "...",
                    "source": "...",
                    "page_number": 1,
                    "section": "...",
                    "file_type": "pdf",
                    "metadata": {...},
                }
            ]

        Returns indexing statistics.
        """

        if not chunks:
            logger.warning(
                "No chunks provided to indexing pipeline"
            )

            return {
                "chunks_received": 0,
                "chunks_indexed": 0,
            }

        logger.info(
            "Starting indexing for %s chunks",
            len(chunks),
        )

        valid_chunks: list[dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = chunk.get("id")
            text = chunk.get("text")

            if not chunk_id:
                logger.warning(
                    "Skipping chunk without id"
                )
                continue

            if not isinstance(text, str) or not text.strip():
                logger.warning(
                    "Skipping empty chunk: %s",
                    chunk_id,
                )
                continue

            valid_chunks.append(chunk)

        if not valid_chunks:
            logger.warning(
                "No valid chunks available for indexing"
            )

            return {
                "chunks_received": len(chunks),
                "chunks_indexed": 0,
            }

        # ---------------------------------------------------------
        # 1. Generate embeddings
        # ---------------------------------------------------------

        logger.info(
            "Generating embeddings for %s chunks",
            len(valid_chunks),
        )

        embedded_chunks = (
            self.embedding_generator.generate(
                valid_chunks
            )
        )

        if not embedded_chunks:
            logger.warning(
                "Embedding generator returned no results"
            )

            return {
                "chunks_received": len(chunks),
                "chunks_indexed": 0,
            }

        # ---------------------------------------------------------
        # 2. Extract vectors and IDs
        # ---------------------------------------------------------

        embeddings: list[Any] = []
        ids: list[str] = []

        for item in embedded_chunks:
            chunk_id = item.get("id")
            embedding = item.get("embedding")

            if not chunk_id:
                logger.warning(
                    "Embedding result has no chunk id"
                )
                continue

            if embedding is None:
                logger.warning(
                    "No embedding generated for chunk %s",
                    chunk_id,
                )
                continue

            ids.append(str(chunk_id))
            embeddings.append(embedding)

        if not embeddings:
            logger.warning(
                "No valid embeddings generated"
            )

            return {
                "chunks_received": len(chunks),
                "chunks_indexed": 0,
            }

        # ---------------------------------------------------------
        # 3. Add vectors to FAISS
        # ---------------------------------------------------------

        logger.info(
            "Adding %s vectors to FAISS",
            len(embeddings),
        )

        self.vector_index.add(
            embeddings,
            ids,
        )

        # ---------------------------------------------------------
        # 4. Persist metadata
        # ---------------------------------------------------------

        metadata_items: list[ChunkMetadata] = []

        # Map IDs back to their original chunks.
        chunk_by_id = {
            str(chunk["id"]): chunk
            for chunk in valid_chunks
        }

        for chunk_id in ids:
            chunk = chunk_by_id.get(chunk_id)

            if chunk is None:
                logger.warning(
                    "Could not find source chunk for metadata: %s",
                    chunk_id,
                )
                continue

            metadata = chunk.get("metadata")

            if not isinstance(metadata, dict):
                metadata = {}

            # Copy so we don't mutate the original dictionary.
            metadata = dict(metadata)

            metadata.setdefault(
                "chunk_id",
                chunk_id,
            )

            if chunk.get("document_id") is not None:
                metadata.setdefault(
                    "document_id",
                    str(chunk["document_id"]),
                )

            if chunk.get("section_id") is not None:
                metadata.setdefault(
                    "section_id",
                    str(chunk["section_id"]),
                )

            if chunk.get("page_number") is not None:
                metadata.setdefault(
                    "page_number",
                    chunk["page_number"],
                )

            if chunk.get("section") is not None:
                metadata.setdefault(
                    "section",
                    chunk["section"],
                )

            metadata_items.append(
                ChunkMetadata(
                    chunk_id=chunk_id,
                    document_id=str(
                        chunk.get(
                            "document_id",
                            "unknown",
                        )
                    ),
                    source=chunk.get(
                        "source"
                    ),
                    text=chunk.get(
                        "text"
                    ),
                    page_number=chunk.get(
                        "page_number"
                    ),
                    section=chunk.get(
                        "section"
                    ),
                    file_type=chunk.get(
                        "file_type"
                    ),
                    extra=metadata,
                )
            )

        if metadata_items:
            logger.info(
                "Persisting metadata for %s chunks",
                len(metadata_items),
            )

            self.metadata_store.add_many(
                metadata_items
            )

        # ---------------------------------------------------------
        # 5. Persist FAISS
        # ---------------------------------------------------------

        logger.info(
            "Persisting FAISS index with %s vectors",
            len(ids),
        )

        self.persistence.save(
            self.vector_index.index,
            self.vector_index.ids,
        )

        logger.info(
            "Indexing completed successfully: %s chunks",
            len(ids),
        )

        return {
            "chunks_received": len(chunks),
            "chunks_indexed": len(ids),
            "vectors_added": len(ids),
            "metadata_items": len(
                metadata_items
            ),
            "vector_dimension": 384,
        }

    def load_existing_index(self) -> bool:
        """
        Restore a previously persisted FAISS index.
        """

        data = self.persistence.load()

        if not data:
            logger.info(
                "No existing FAISS index found"
            )
            return False

        self.vector_index.index = data["index"]
        self.vector_index.ids = data["ids"]

        logger.info(
            "Existing FAISS index restored: %s vectors",
            len(self.vector_index.ids),
        )

        return True

    def search(
        self,
        query_embedding: Any,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Search the FAISS index and resolve metadata.
        """

        if top_k <= 0:
            return {
                "results": [],
                "documents": [],
            }

        results = self.vector_index.search(
            query_embedding,
            top_k,
        )

        if not results:
            return {
                "results": [],
                "documents": [],
            }

        chunk_ids = [
            str(item["id"])
            for item in results
            if item.get("id") is not None
        ]

        metadata = self.metadata_store.get_many(
            chunk_ids
        )

        return {
            "results": results,
            "documents": metadata,
        }