from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .collector import EvidenceItem


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    """
    Provenance information for a piece of evidence.
    """

    evidence_id: str

    document_id: str | None
    chunk_id: str | None

    source: str | None
    source_type: str | None

    metadata: Mapping[str, Any]

    completeness: float


class ProvenanceTracker:
    """
    Extracts and scores provenance quality.

    This class does not attempt to determine whether a source is
    factually correct. It only evaluates traceability.
    """

    def __init__(
        self,
        *,
        require_source: bool = True,
        require_document_id: bool = False,
        require_chunk_id: bool = False,
    ) -> None:
        self.require_source = require_source
        self.require_document_id = require_document_id
        self.require_chunk_id = require_chunk_id

    def inspect(
        self,
        item: EvidenceItem,
    ) -> ProvenanceRecord:
        completeness = self._completeness(item)

        return ProvenanceRecord(
            evidence_id=item.evidence_id,
            document_id=item.document_id,
            chunk_id=item.chunk_id,
            source=item.source,
            source_type=item.source_type,
            metadata=dict(item.metadata),
            completeness=completeness,
        )

    def inspect_many(
        self,
        evidence: Iterable[EvidenceItem],
    ) -> tuple[ProvenanceRecord, ...]:
        return tuple(
            self.inspect(item)
            for item in evidence
        )

    def score(
        self,
        item: EvidenceItem,
    ) -> float:
        return self.inspect(item).completeness

    def _completeness(
        self,
        item: EvidenceItem,
    ) -> float:
        checks: list[bool] = []

        if self.require_source:
            checks.append(bool(item.source))

        if self.require_document_id:
            checks.append(bool(item.document_id))

        if self.require_chunk_id:
            checks.append(bool(item.chunk_id))

        if item.provenance:
            checks.append(True)

        if not checks:
            return 1.0

        return sum(checks) / len(checks)

    @staticmethod
    def source_key(
        item: EvidenceItem,
    ) -> str:
        """
        Stable source identity used by corroboration and coverage.
        """

        if item.source:
            return item.source

        if item.document_id:
            return item.document_id

        return item.evidence_id