"""
Evidence provenance models.

Provenance tracks where a retrieved piece of evidence came from so that
downstream RAG components can provide traceable citations and explanations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional
from uuid import UUID


@dataclass(slots=True)
class EvidenceProvenance:
    """
    Describes the origin of a piece of evidence.

    All identifiers are optional because different retrievers may provide
    different levels of metadata.
    """

    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    paper_id: Optional[str] = None

    source_type: Optional[str] = None
    source_uri: Optional[str] = None

    title: Optional[str] = None
    page_number: Optional[int] = None

    section: Optional[str] = None
    author: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize provenance to a JSON-compatible dictionary."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "source_type": self.source_type,
            "source_uri": self.source_uri,
            "title": self.title,
            "page_number": self.page_number,
            "section": self.section,
            "author": self.author,
            "metadata": self.metadata,
        }

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any] | None,
    ) -> "EvidenceProvenance":
        """
        Build provenance from arbitrary retriever metadata.
        """
        if not data:
            return cls()

        return cls(
            document_id=_string_value(data.get("document_id")),
            chunk_id=_string_value(data.get("chunk_id")),
            paper_id=_string_value(data.get("paper_id")),
            source_type=_string_value(data.get("source_type")),
            source_uri=_string_value(
                data.get("source_uri") or data.get("url")
            ),
            title=_string_value(data.get("title")),
            page_number=_int_value(
                data.get("page_number") or data.get("page")
            ),
            section=_string_value(data.get("section")),
            author=_string_value(data.get("author")),
            metadata=dict(data),
        )


class ProvenanceBuilder:
    """
    Utility for extracting provenance from retrieval result objects.

    The retriever layer may use dictionaries, Pydantic models, dataclasses,
    or ORM-like objects. This class intentionally avoids coupling the
    evidence layer to any particular representation.
    """

    @staticmethod
    def build(result: Any) -> EvidenceProvenance:
        """Extract provenance from a retrieval result."""

        if isinstance(result, EvidenceProvenance):
            return result

        if isinstance(result, Mapping):
            metadata = result.get("metadata")

            if isinstance(metadata, Mapping):
                merged = dict(metadata)
                merged.update(result)
                return EvidenceProvenance.from_mapping(merged)

            return EvidenceProvenance.from_mapping(result)

        values: dict[str, Any] = {}

        for field_name in (
            "document_id",
            "chunk_id",
            "paper_id",
            "source_type",
            "source_uri",
            "url",
            "title",
            "page_number",
            "page",
            "section",
            "author",
            "metadata",
        ):
            value = getattr(result, field_name, None)

            if value is not None:
                values[field_name] = value

        metadata = getattr(result, "metadata", None)

        if isinstance(metadata, Mapping):
            merged = dict(metadata)
            merged.update(values)
            values = merged

        return EvidenceProvenance.from_mapping(values)


def _string_value(value: Any) -> Optional[str]:
    """Safely convert identifiers and strings to strings."""

    if value is None:
        return None

    if isinstance(value, UUID):
        return str(value)

    return str(value)


def _int_value(value: Any) -> Optional[int]:
    """Safely convert a value to an integer."""

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None