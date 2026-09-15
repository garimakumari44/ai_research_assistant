from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence

from .collector import EvidenceItem
from .provenance import ProvenanceTracker


@dataclass(frozen=True, slots=True)
class CorroborationResult:
    """
    Measures independent source support for retrieved evidence.
    """

    score: float

    evidence_count: int
    unique_sources: int

    source_groups: tuple[tuple[str, tuple[str, ...]], ...]

    independently_supported: bool


class CorroborationEvaluator:
    """
    Evaluates whether evidence is supported by multiple sources.

    Important:
        Multiple chunks from the same document do NOT count as
        independent corroboration.
    """

    def __init__(
        self,
        *,
        independent_source_threshold: int = 2,
    ) -> None:
        if independent_source_threshold < 1:
            raise ValueError(
                "independent_source_threshold must be >= 1"
            )

        self.independent_source_threshold = (
            independent_source_threshold
        )

        self.provenance = ProvenanceTracker()

    def evaluate(
        self,
        evidence: Sequence[EvidenceItem],
    ) -> CorroborationResult:
        groups: dict[str, list[str]] = defaultdict(list)

        for item in evidence:
            source = self.provenance.source_key(item)

            groups[source].append(item.evidence_id)

        unique_sources = len(groups)

        if not evidence:
            return CorroborationResult(
                score=0.0,
                evidence_count=0,
                unique_sources=0,
                source_groups=(),
                independently_supported=False,
            )

        source_score = min(
            1.0,
            unique_sources
            / self.independent_source_threshold,
        )

        source_groups = tuple(
            (source, tuple(ids))
            for source, ids in sorted(groups.items())
        )

        return CorroborationResult(
            score=source_score,
            evidence_count=len(evidence),
            unique_sources=unique_sources,
            source_groups=source_groups,
            independently_supported=(
                unique_sources
                >= self.independent_source_threshold
            ),
        )

    def source_count(
        self,
        evidence: Iterable[EvidenceItem],
    ) -> int:
        return len(
            {
                self.provenance.source_key(item)
                for item in evidence
            }
        )