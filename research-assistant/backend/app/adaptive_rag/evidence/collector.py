from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """
    Normalized evidence unit consumed by the adaptive RAG evidence layer.

    The collector deliberately does not depend on a concrete retrieval
    implementation. Retrieval systems may return dataclasses, Pydantic
    models, dictionaries, or lightweight objects.
    """

    evidence_id: str
    content: str

    score: float = 0.0
    rank: int = 0

    document_id: str | None = None
    chunk_id: str | None = None

    source: str | None = None
    source_type: str | None = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id cannot be empty")

        if not self.content.strip():
            raise ValueError("Evidence content cannot be empty")

        if self.rank < 0:
            raise ValueError("rank cannot be negative")


@dataclass(frozen=True, slots=True)
class EvidenceCollection:
    """
    Immutable collection of normalized evidence.
    """

    query: str
    items: tuple[EvidenceItem, ...]
    total_collected: int
    deduplicated: int

    @property
    def is_empty(self) -> bool:
        return not self.items

    @property
    def top_score(self) -> float:
        if not self.items:
            return 0.0

        return max(item.score for item in self.items)

    @property
    def sources(self) -> tuple[str, ...]:
        values = {
            item.source
            for item in self.items
            if item.source
        }

        return tuple(sorted(values))


class EvidenceCollector:
    """
    Converts retrieval results into normalized evidence.

    Responsibilities:
        - normalize retrieval outputs
        - remove invalid evidence
        - deduplicate identical chunks
        - preserve retrieval ranking
        - enforce maximum evidence count

    Non-responsibilities:
        - retrieval
        - LLM generation
        - contradiction reasoning
        - final answer generation
    """

    def __init__(
        self,
        *,
        max_items: int = 20,
        min_content_length: int = 10,
        deduplicate: bool = True,
    ) -> None:
        if max_items <= 0:
            raise ValueError("max_items must be greater than zero")

        if min_content_length < 0:
            raise ValueError("min_content_length cannot be negative")

        self.max_items = max_items
        self.min_content_length = min_content_length
        self.deduplicate = deduplicate

    def collect(
        self,
        query: str,
        results: Iterable[Any] | None,
    ) -> EvidenceCollection:
        """
        Normalize retrieval results into EvidenceCollection.
        """

        if not query or not query.strip():
            raise ValueError("query cannot be empty")

        if results is None:
            return EvidenceCollection(
                query=query,
                items=(),
                total_collected=0,
                deduplicated=0,
            )

        normalized: list[EvidenceItem] = []
        seen: set[str] = set()
        total = 0

        for index, result in enumerate(results):
            total += 1

            try:
                item = self._normalize(result, index)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Skipping invalid retrieval result",
                    extra={
                        "index": index,
                        "error": str(exc),
                    },
                )
                continue

            if len(item.content.strip()) < self.min_content_length:
                continue

            if self.deduplicate:
                key = self._deduplication_key(item)

                if key in seen:
                    continue

                seen.add(key)

            normalized.append(item)

            if len(normalized) >= self.max_items:
                break

        normalized.sort(
            key=lambda item: (
                -item.score,
                item.rank,
            )
        )

        return EvidenceCollection(
            query=query,
            items=tuple(normalized),
            total_collected=total,
            deduplicated=total - len(normalized),
        )

    def _normalize(
        self,
        result: Any,
        index: int,
    ) -> EvidenceItem:
        content = self._get(
            result,
            "content",
            "text",
            "page_content",
            default="",
        )

        if content is None:
            content = ""

        content = str(content).strip()

        if not content:
            raise ValueError("retrieval result has no content")

        evidence_id = self._get(
            result,
            "evidence_id",
            "id",
            "chunk_id",
            default=None,
        )

        document_id = self._get(
            result,
            "document_id",
            "doc_id",
            default=None,
        )

        chunk_id = self._get(
            result,
            "chunk_id",
            default=None,
        )

        if evidence_id is None:
            evidence_id = (
                f"{document_id or 'document'}:"
                f"{chunk_id or index}"
            )

        score = self._safe_float(
            self._get(
                result,
                "score",
                "similarity",
                "relevance_score",
                default=0.0,
            )
        )

        rank = self._safe_int(
            self._get(
                result,
                "rank",
                default=index,
            ),
            default=index,
        )

        source = self._get(
            result,
            "source",
            "source_url",
            "uri",
            default=None,
        )

        source_type = self._get(
            result,
            "source_type",
            "type",
            default=None,
        )

        metadata = self._get(
            result,
            "metadata",
            default={},
        )

        if not isinstance(metadata, Mapping):
            metadata = {}

        provenance = self._get(
            result,
            "provenance",
            default={},
        )

        if not isinstance(provenance, Mapping):
            provenance = {}

        return EvidenceItem(
            evidence_id=str(evidence_id),
            content=content,
            score=score,
            rank=rank,
            document_id=(
                str(document_id)
                if document_id is not None
                else None
            ),
            chunk_id=(
                str(chunk_id)
                if chunk_id is not None
                else None
            ),
            source=(
                str(source)
                if source is not None
                else None
            ),
            source_type=(
                str(source_type)
                if source_type is not None
                else None
            ),
            metadata=dict(metadata),
            provenance=dict(provenance),
        )

    @staticmethod
    def _get(
        obj: Any,
        *names: str,
        default: Any = None,
    ) -> Any:
        for name in names:
            if isinstance(obj, Mapping):
                if name in obj:
                    return obj[name]

            elif hasattr(obj, name):
                return getattr(obj, name)

        return default

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            result = float(value)

            if result != result:
                return 0.0

            if result in (float("inf"), float("-inf")):
                return 0.0

            return result
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_int(
        value: Any,
        *,
        default: int,
    ) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _deduplication_key(item: EvidenceItem) -> str:
        """
        Prefer stable chunk/document identifiers.

        Fall back to normalized content.
        """

        if item.document_id and item.chunk_id:
            return f"{item.document_id}:{item.chunk_id}"

        return " ".join(item.content.lower().split())