"""
Application-level retrieval service.

The RetrievalService is the stable application boundary for retrieval.

Consumers include:

- Explore
- Adaptive RAG
- Research Engine
- Research agents
- API routes

The service does not implement retrieval algorithms.

Architecture:

    RetrievalQuery
          ↓
    RetrievalService
          ↓
    RetrievalPipeline
          ↓
    Query Processing
          ↓
    Routing
          ↓
    Planning
          ↓
    Dense / Sparse Retrieval
          ↓
    Hybrid Fusion
          ↓
    RRF
          ↓
    Document Resolution
          ↓
    Metadata Filtering
          ↓
    Cross Encoder
          ↓
    RetrievalResult
          ↓
    RetrievalResponse
"""

from __future__ import annotations

from typing import Any

from app.knowledge.indexing.registry import IndexRegistry

from app.retrieval.models import (
    RetrievalQuery,
    RetrievalResponse,
)

from app.retrieval.pipeline import RetrievalPipeline

from app.schemas.retrieval import (
    RetrievalResponse as APIRetrievalResponse,
)


class RetrievalService:
    """
    Stable application-level retrieval boundary.

    Responsibilities
    ----------------
    - Own the application retrieval contract.
    - Coordinate RetrievalPipeline.
    - Convert internal retrieval responses to API responses.
    - Provide convenient programmatic retrieval methods.

    Non-responsibilities
    --------------------
    - Vector search implementation.
    - BM25 implementation.
    - Fusion implementation.
    - RRF implementation.
    - Reranking implementation.
    - Index ownership.
    """

    def __init__(
        self,
        *,
        pipeline: RetrievalPipeline | None = None,
        registry: IndexRegistry | None = None,
        documents: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize RetrievalService.

        Preferred production composition:

            service = RetrievalService(
                registry=shared_registry,
            )

        The same IndexRegistry must be shared by indexing and retrieval.
        """

        # --------------------------------------------------------------
        # Existing pipeline
        # --------------------------------------------------------------

        if pipeline is not None:
            self.pipeline = pipeline
            return

        # --------------------------------------------------------------
        # Shared registry is mandatory
        # --------------------------------------------------------------

        if registry is None:
            raise ValueError(
                "registry must be provided when a "
                "RetrievalPipeline is not supplied."
            )

        # --------------------------------------------------------------
        # Construct canonical pipeline
        # --------------------------------------------------------------

        self.pipeline = RetrievalPipeline(
            documents=documents or [],
            index_registry=registry,
        )

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        request: RetrievalQuery,
    ) -> RetrievalResponse:
        """
        Execute retrieval using the canonical RetrievalQuery.

        The service deliberately does not manipulate the query after
        construction. Query processing belongs to RetrievalPipeline.
        """

        if not isinstance(
            request,
            RetrievalQuery,
        ):
            raise TypeError(
                "request must be a RetrievalQuery instance."
            )

        return await self.pipeline.retrieve(
            request
        )

    # ==================================================================
    # API RESPONSE CONVERSION
    # ==================================================================

    def to_api_response(
        self,
        response: RetrievalResponse,
    ) -> APIRetrievalResponse:
        """
        Convert internal RetrievalResponse into the public API schema.
        """

        if not isinstance(
            response,
            RetrievalResponse,
        ):
            raise TypeError(
                "response must be a RetrievalResponse instance."
            )

        return APIRetrievalResponse(
            query=response.query,
            results=[
                self._to_api_result(
                    result
                )
                for result in response.results
            ],
            total=response.total_results,
            top_k=len(response.results),
            retrieval_mode=response.retrieval_mode.value,
            metadata=response.metadata,
        )

    # ==================================================================
    # API RESULT
    # ==================================================================

    @staticmethod
    def _to_api_result(
        result: Any,
    ) -> dict[str, Any]:
        """
        Convert one internal RetrievalResult to the API representation.
        """

        document = result.document

        return {
            "chunk_id": document.chunk_id,
            "document_id": document.document_id,
            "paper_id": document.paper_id,
            "section_id": None,

            "content": document.text,

            "score": result.score,
            "rank": result.rank,

            "retrieval_method": (
                result.retrieval_method.value
            ),

            "rerank_score": result.rerank_score,
            "vector_score": result.vector_score,
            "keyword_score": result.keyword_score,

            "provenance": None,
            "evidence": None,

            "metadata": {
                **document.metadata,
                **result.metadata,
            },
        }

    # ==================================================================
    # CONVENIENCE RETRIEVE
    # ==================================================================

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 10,
        mode: str = "hybrid",
        filters: dict[str, Any] | None = None,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        metadata: dict[str, Any] | None = None,
        enable_reranking: bool = True,
    ) -> RetrievalResponse:
        """
        Convenience API for programmatic retrieval.

        Converts a simple query into the canonical RetrievalQuery model.
        """

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query must not be empty."
            )

        request = RetrievalQuery(
            query=query,
            top_k=top_k,
            mode=mode,
            filters=filters or {},
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
            metadata=metadata or {},
            enable_reranking=enable_reranking,
        )

        return await self.search(
            request
        )

    # ==================================================================
    # RETRIEVE DOCUMENTS
    # ==================================================================

    async def retrieve_documents(
        self,
        query: str,
        *,
        top_k: int = 10,
        mode: str = "hybrid",
        filters: dict[str, Any] | None = None,
        enable_reranking: bool = True,
    ) -> list[Any]:
        """
        Convenience API returning only RetrievedDocument objects.

        Useful for:

        - Research agents
        - Adaptive RAG
        - Evidence collection
        - Synthesis
        - Programmatic consumers
        """

        response = await self.retrieve(
            query,
            top_k=top_k,
            mode=mode,
            filters=filters,
            enable_reranking=enable_reranking,
        )

        return [
            result.document
            for result in response.results
        ]


__all__ = [
    "RetrievalService",
]