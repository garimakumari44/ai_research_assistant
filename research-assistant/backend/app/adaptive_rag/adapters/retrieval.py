"""
Adaptive RAG retrieval adapter.

This module bridges the Adaptive RAG orchestration layer with the
application retrieval layer.

Adaptive RAG strategies depend on a small, stable interface:

    await retriever.retrieve(
        query,
        top_k=5,
        ...
    )

The application retrieval layer exposes:

    await RetrievalService.search(
        RetrievalQuery(...)
    )

This adapter deliberately keeps those contracts separate.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence
from uuid import UUID

from app.retrieval.models import (
    RetrievalMode,
    RetrievalQuery,
    RetrievalResult,
)
from app.retrieval.service import RetrievalService


class RetrievalAdapter:
    """
    Adapter between Adaptive RAG and the application RetrievalService.

    Supported interface:

        await adapter.retrieve(
            query,
            top_k=5,
            ...
        )

    and:

        await adapter.search(
            query,
            top_k=5,
            ...
        )
    """

    # ------------------------------------------------------------------
    # Validation limits
    # ------------------------------------------------------------------

    DEFAULT_TOP_K: int = 5
    MIN_TOP_K: int = 1
    MAX_TOP_K: int = 100

    DEFAULT_VECTOR_WEIGHT: float = 0.5
    DEFAULT_KEYWORD_WEIGHT: float = 0.5

    # Only retrieval-specific parameters may cross this boundary.
    SUPPORTED_KWARGS: frozenset[str] = frozenset(
        {
            "paper_id",
            "document_id",
            "vector_weight",
            "keyword_weight",
            "mode",
            "filters",
            "metadata",
        }
    )

    def __init__(
        self,
        retrieval_service: RetrievalService,
    ) -> None:

        if retrieval_service is None:
            raise ValueError(
                "retrieval_service must not be None"
            )

        self.retrieval_service = retrieval_service

    # ==================================================================
    # Main Adaptive RAG interface
    # ==================================================================

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        **kwargs: Any,
    ) -> Sequence[RetrievalResult]:
        """
        Retrieve evidence for an Adaptive RAG strategy.
        """

        normalized_query = self._normalize_query(
            query
        )

        normalized_top_k = self._normalize_top_k(
            top_k
        )

        self._validate_kwargs(
            kwargs
        )

        request = self._build_request(
            query=normalized_query,
            top_k=normalized_top_k,
            kwargs=kwargs,
        )

        response = await self.retrieval_service.search(
            request
        )

        if response is None:
            raise RuntimeError(
                "RetrievalService.search() returned None"
            )

        results = getattr(
            response,
            "results",
            None,
        )

        if results is None:
            raise RuntimeError(
                "RetrievalService response does not contain "
                "a 'results' field"
            )

        return results

    # ==================================================================
    # Search compatibility interface
    # ==================================================================

    async def search(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        **kwargs: Any,
    ) -> Sequence[RetrievalResult]:
        """
        Compatibility alias for retrieve().
        """

        return await self.retrieve(
            query,
            top_k=top_k,
            **kwargs,
        )

    # ==================================================================
    # Request construction
    # ==================================================================

    @classmethod
    def _build_request(
        cls,
        *,
        query: str,
        top_k: int,
        kwargs: Mapping[str, Any],
    ) -> RetrievalQuery:
        """
        Convert Adaptive RAG retrieval parameters into RetrievalQuery.

        RetrievalQuery is the canonical request model entering the
        retrieval subsystem.
        """

        request_data: dict[str, Any] = {
            "query": query,
            "top_k": top_k,
        }

        # --------------------------------------------------------------
        # Retrieval mode
        # --------------------------------------------------------------

        mode = kwargs.get(
            "mode"
        )

        if mode is not None:
            request_data["mode"] = (
                cls._normalize_mode(
                    mode
                )
            )

        # --------------------------------------------------------------
        # Filters
        # --------------------------------------------------------------

        filters = kwargs.get(
            "filters"
        )

        if filters is not None:
            if not isinstance(
                filters,
                Mapping,
            ):
                raise TypeError(
                    "filters must be a mapping"
                )

            request_data["filters"] = dict(
                filters
            )

        # --------------------------------------------------------------
        # Metadata
        # --------------------------------------------------------------

        metadata = kwargs.get(
            "metadata"
        )

        if metadata is not None:
            if not isinstance(
                metadata,
                Mapping,
            ):
                raise TypeError(
                    "metadata must be a mapping"
                )

            request_data["metadata"] = dict(
                metadata
            )

        # --------------------------------------------------------------
        # Paper ID
        #
        # papers.id is INTEGER in this application.
        # It must NOT be normalized as a UUID.
        # --------------------------------------------------------------

        paper_id = kwargs.get(
            "paper_id"
        )

        if paper_id is not None:
            normalized_paper_id = (
                cls._normalize_paper_id(
                    paper_id
                )
            )

            request_data["filters"] = {
                **request_data.get(
                    "filters",
                    {},
                ),
                "paper_id": normalized_paper_id,
            }

        # --------------------------------------------------------------
        # Document ID
        #
        # documents.id is UUID.
        # --------------------------------------------------------------

        document_id = kwargs.get(
            "document_id"
        )

        if document_id is not None:
            normalized_document_id = (
                cls._normalize_uuid(
                    document_id
                )
            )

            request_data["filters"] = {
                **request_data.get(
                    "filters",
                    {},
                ),
                "document_id": str(
                    normalized_document_id
                ),
            }

        # --------------------------------------------------------------
        # Hybrid retrieval weights
        # --------------------------------------------------------------

        vector_weight = kwargs.get(
            "vector_weight"
        )

        if vector_weight is not None:
            request_data["vector_weight"] = (
                cls._normalize_weight(
                    vector_weight,
                    field_name="vector_weight",
                )
            )

        keyword_weight = kwargs.get(
            "keyword_weight"
        )

        if keyword_weight is not None:
            request_data["keyword_weight"] = (
                cls._normalize_weight(
                    keyword_weight,
                    field_name="keyword_weight",
                )
            )

        cls._validate_weights(
            vector_weight=request_data.get(
                "vector_weight"
            ),
            keyword_weight=request_data.get(
                "keyword_weight"
            ),
        )

        return RetrievalQuery(
            **request_data
        )

    # ==================================================================
    # Query validation
    # ==================================================================

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:
        """
        Normalize and validate a retrieval query.
        """

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "query must be a string, "
                f"got {type(query).__name__}"
            )

        normalized = query.strip()

        if not normalized:
            raise ValueError(
                "Retrieval query must not be empty"
            )

        return normalized

    # ==================================================================
    # top_k validation
    # ==================================================================

    @classmethod
    def _normalize_top_k(
        cls,
        top_k: int,
    ) -> int:
        """
        Validate the requested number of retrieval results.
        """

        if (
            isinstance(
                top_k,
                bool,
            )
            or not isinstance(
                top_k,
                int,
            )
        ):
            raise TypeError(
                "top_k must be an integer"
            )

        if not cls.MIN_TOP_K <= top_k <= cls.MAX_TOP_K:
            raise ValueError(
                "top_k must be between "
                f"{cls.MIN_TOP_K} and {cls.MAX_TOP_K}; "
                f"got {top_k}"
            )

        return top_k

    # ==================================================================
    # Kwarg validation
    # ==================================================================

    @classmethod
    def _validate_kwargs(
        cls,
        kwargs: Mapping[str, Any],
    ) -> None:
        """
        Reject unsupported Adaptive RAG retrieval arguments.
        """

        unsupported = set(
            kwargs
        ).difference(
            cls.SUPPORTED_KWARGS
        )

        if unsupported:

            names = ", ".join(
                sorted(
                    str(value)
                    for value in unsupported
                )
            )

            raise TypeError(
                "Unsupported retrieval parameter(s): "
                f"{names}"
            )

    # ==================================================================
    # Retrieval mode normalization
    # ==================================================================

    @staticmethod
    def _normalize_mode(
        value: Any,
    ) -> RetrievalMode:
        """
        Normalize a retrieval mode into the canonical RetrievalMode enum.
        """

        if isinstance(
            value,
            RetrievalMode,
        ):
            return value

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "mode must be a RetrievalMode or string"
            )

        normalized = value.strip().lower()

        aliases = {
            "vector": RetrievalMode.DENSE,
            "dense": RetrievalMode.DENSE,
            "keyword": RetrievalMode.BM25,
            "bm25": RetrievalMode.BM25,
            "sparse": RetrievalMode.BM25,
            "hybrid": RetrievalMode.HYBRID,
        }

        try:
            return aliases[
                normalized
            ]
        except KeyError as exc:
            raise ValueError(
                "Unsupported retrieval mode: "
                f"{value!r}. Expected one of: "
                "dense, bm25, hybrid"
            ) from exc

    # ==================================================================
    # Paper ID normalization
    # ==================================================================

    @staticmethod
    def _normalize_paper_id(
        value: Any,
    ) -> int:
        """
        Normalize a paper database ID.

        papers.id is an integer.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "paper_id must be an integer"
            )

        try:
            normalized = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                "paper_id must be an integer"
            ) from exc

        if normalized <= 0:
            raise ValueError(
                "paper_id must be greater than 0"
            )

        return normalized

    # ==================================================================
    # Weight validation
    # ==================================================================

    @staticmethod
    def _normalize_weight(
        value: Any,
        *,
        field_name: str,
    ) -> float:
        """
        Convert and validate a retrieval weight.

        Weights must be finite and within [0, 1].
        """

        try:
            normalized = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                f"{field_name} must be a numeric value"
            ) from exc

        if not math.isfinite(
            normalized
        ):
            raise ValueError(
                f"{field_name} must be finite"
            )

        if not 0.0 <= normalized <= 1.0:
            raise ValueError(
                f"{field_name} must be between 0.0 and 1.0; "
                f"got {normalized}"
            )

        return normalized

    @staticmethod
    def _validate_weights(
        *,
        vector_weight: float | None,
        keyword_weight: float | None,
    ) -> None:
        """
        Validate the relationship between hybrid retrieval weights.

        If one or both weights are supplied, their effective sum must
        be greater than zero.
        """

        if (
            vector_weight is None
            and keyword_weight is None
        ):
            return

        vector = (
            0.0
            if vector_weight is None
            else float(vector_weight)
        )

        keyword = (
            0.0
            if keyword_weight is None
            else float(keyword_weight)
        )

        if vector + keyword <= 0.0:
            raise ValueError(
                "At least one retrieval weight must be greater than 0"
            )

    # ==================================================================
    # UUID normalization
    # ==================================================================

    @staticmethod
    def _normalize_uuid(
        value: UUID | str,
    ) -> UUID:
        """
        Normalize a UUID supplied by Adaptive RAG.
        """

        if isinstance(
            value,
            UUID,
        ):
            return value

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "UUID value must be a UUID instance or string"
            )

        try:
            return UUID(
                value
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid UUID value: {value!r}"
            ) from exc


__all__ = [
    "RetrievalAdapter",
]