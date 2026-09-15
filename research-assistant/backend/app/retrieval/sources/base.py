from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.retrieval.advanced.models import RetrievalSource
from app.retrieval.models import RetrievedDocument


class BaseRetrievalSource(ABC):
    """
    Canonical interface for an Explore retrieval source.

    Sources are responsible for executing retrieval against one
    backend. They do not perform:

        - query classification
        - query rewriting
        - query decomposition
        - source selection
        - result synthesis

    Those responsibilities belong to the higher-level orchestration
    layer.

    Every source returns the canonical RetrievedDocument model so that
    downstream components do not need to know the implementation
    details of a particular source.
    """

    source_type: RetrievalSource

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.source_type.value

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedDocument]:
        """
        Execute retrieval against this source.
        """
        raise NotImplementedError

    def normalize_result(
        self,
        result: Any,
        *,
        default_source: str | None = None,
        default_score: float = 0.0,
    ) -> RetrievedDocument:
        """
        Normalize a backend-specific result into RetrievedDocument.

        This method intentionally accepts several common result shapes
        because external providers may return dictionaries or objects.
        """

        if isinstance(result, RetrievedDocument):
            return result

        source = default_source or self.name

        if isinstance(result, dict):
            raw_id = (
                result.get("id")
                or result.get("chunk_id")
                or result.get("document_id")
                or result.get("paper_id")
            )

            content = (
                result.get("content")
                or result.get("text")
                or result.get("page_content")
                or ""
            )

            raw_score = result.get(
                "score",
                default_score,
            )

            metadata = result.get("metadata") or {}

            return RetrievedDocument(
                id=str(raw_id or ""),
                content=str(content),
                source=str(
                    result.get(
                        "source",
                        source,
                    )
                ),
                score=self._safe_score(
                    raw_score,
                    default_score,
                ),
                metadata=dict(metadata),
            )

        raw_id = (
            getattr(result, "id", None)
            or getattr(result, "chunk_id", None)
            or getattr(result, "document_id", None)
            or getattr(result, "paper_id", None)
        )

        content = (
            getattr(result, "content", None)
            or getattr(result, "text", None)
            or getattr(result, "page_content", None)
            or ""
        )

        raw_score = getattr(
            result,
            "score",
            default_score,
        )

        metadata = getattr(
            result,
            "metadata",
            {},
        )

        return RetrievedDocument(
            id=str(raw_id or ""),
            content=str(content),
            source=str(
                getattr(
                    result,
                    "source",
                    source,
                )
            ),
            score=self._safe_score(
                raw_score,
                default_score,
            ),
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _safe_score(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            score = float(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return float(default)

        if score != score:
            return float(default)

        if abs(score) == float("inf"):
            return float(default)

        return score