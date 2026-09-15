from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .collector import EvidenceItem
from .contradiction import (
    ContradictionDetector,
    ContradictionResult,
)
from .corroboration import (
    CorroborationEvaluator,
    CorroborationResult,
)
from .coverage import (
    CoverageResult,
    EvidenceCoverageEvaluator,
)
from .provenance import ProvenanceTracker


@dataclass(frozen=True, slots=True)
class EvidenceScore:
    """
    Individual evidence quality score.
    """

    evidence_id: str

    relevance: float
    provenance: float

    final_score: float


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    """
    Complete evidence-layer assessment.

    This object is suitable for consumption by the adaptive controller
    and stopping policy.
    """

    overall_score: float

    evidence_count: int
    unique_sources: int

    coverage: CoverageResult
    corroboration: CorroborationResult
    contradiction: ContradictionResult

    individual_scores: tuple[EvidenceScore, ...]

    sufficient: bool
    needs_refinement: bool


class EvidenceScorer:
    """
    Aggregates evidence quality into a single deterministic assessment.

    Default weighting:

        relevance       35%
        coverage        25%
        corroboration   15%
        provenance      10%
        contradiction   15%

    Contradiction is treated as a penalty.
    """

    def __init__(
        self,
        *,
        relevance_weight: float = 0.35,
        coverage_weight: float = 0.25,
        corroboration_weight: float = 0.15,
        provenance_weight: float = 0.10,
        contradiction_weight: float = 0.15,
        sufficiency_threshold: float = 0.70,
    ) -> None:
        weights = (
            relevance_weight,
            coverage_weight,
            corroboration_weight,
            provenance_weight,
            contradiction_weight,
        )

        if any(weight < 0 for weight in weights):
            raise ValueError(
                "Evidence weights cannot be negative"
            )

        total = sum(weights)

        if total <= 0:
            raise ValueError(
                "Evidence weights must sum to a positive value"
            )

        self.relevance_weight = relevance_weight / total
        self.coverage_weight = coverage_weight / total
        self.corroboration_weight = corroboration_weight / total
        self.provenance_weight = provenance_weight / total
        self.contradiction_weight = contradiction_weight / total

        if not 0.0 <= sufficiency_threshold <= 1.0:
            raise ValueError(
                "sufficiency_threshold must be between 0 and 1"
            )

        self.sufficiency_threshold = sufficiency_threshold

        self.coverage = EvidenceCoverageEvaluator()
        self.corroboration = CorroborationEvaluator()
        self.contradiction = ContradictionDetector()
        self.provenance = ProvenanceTracker()

    def score(
        self,
        query: str,
        evidence: Sequence[EvidenceItem],
    ) -> EvidenceAssessment:
        coverage = self.coverage.evaluate(
            query,
            evidence,
        )

        corroboration = self.corroboration.evaluate(
            evidence
        )

        contradiction = self.contradiction.evaluate(
            evidence
        )

        individual_scores = tuple(
            self._score_item(item)
            for item in evidence
        )

        relevance = self._aggregate_relevance(
            individual_scores
        )

        provenance = self._aggregate_provenance(
            evidence
        )

        overall = (
            relevance * self.relevance_weight
            + coverage.score * self.coverage_weight
            + corroboration.score
            * self.corroboration_weight
            + provenance * self.provenance_weight
            + contradiction.score
            * self.contradiction_weight
        )

        overall = max(0.0, min(1.0, overall))

        sufficient = (
            overall >= self.sufficiency_threshold
            and coverage.sufficient
            and not contradiction.has_contradiction
        )

        needs_refinement = (
            not sufficient
            or coverage.score < 0.5
            or contradiction.has_contradiction
        )

        return EvidenceAssessment(
            overall_score=overall,
            evidence_count=len(evidence),
            unique_sources=corroboration.unique_sources,
            coverage=coverage,
            corroboration=corroboration,
            contradiction=contradiction,
            individual_scores=individual_scores,
            sufficient=sufficient,
            needs_refinement=needs_refinement,
        )

    def _score_item(
        self,
        item: EvidenceItem,
    ) -> EvidenceScore:
        relevance = self._normalize_relevance(
            item.score
        )

        provenance = self.provenance.score(item)

        final_score = (
            relevance * 0.75
            + provenance * 0.25
        )

        return EvidenceScore(
            evidence_id=item.evidence_id,
            relevance=relevance,
            provenance=provenance,
            final_score=final_score,
        )

    @staticmethod
    def _normalize_relevance(
        score: float,
    ) -> float:
        """
        Retrieval scores are not guaranteed to use the same range.

        Clamp rather than assuming a particular retrieval implementation.
        """

        if score != score:
            return 0.0

        if score <= 0:
            return 0.0

        if score >= 1:
            return 1.0

        return score

    @staticmethod
    def _aggregate_relevance(
        scores: Sequence[EvidenceScore],
    ) -> float:
        if not scores:
            return 0.0

        # Give stronger evidence more influence while preventing
        # a large number of weak chunks from dominating the score.
        sorted_scores = sorted(
            (
                score.final_score
                for score in scores
            ),
            reverse=True,
        )

        top_k = sorted_scores[:5]

        if not top_k:
            return 0.0

        weighted_sum = 0.0
        weight_sum = 0.0

        for index, score in enumerate(top_k):
            weight = 1.0 / (index + 1)

            weighted_sum += score * weight
            weight_sum += weight

        return weighted_sum / weight_sum

    def _aggregate_provenance(
        self,
        evidence: Sequence[EvidenceItem],
    ) -> float:
        if not evidence:
            return 0.0

        values = [
            self.provenance.score(item)
            for item in evidence
        ]

        return sum(values) / len(values)