from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ingestion.processing.confidence import (
    PaperConfidenceScorer,
)
from app.ingestion.processing.deduplicator import (
    PaperDeduplicator,
)
from app.ingestion.processing.normalizer import (
    PaperNormalizer,
)
from app.ingestion.processing.resolver import (
    PaperResolver,
)
from app.ingestion.processing.validator import (
    PaperValidator,
)


@dataclass
class PaperProcessingResult:
    """
    Result produced by the paper processing pipeline.
    """

    paper: dict[str, Any]
    identity_key: str
    confidence_score: float
    confidence_level: str


class PaperProcessingPipeline:
    """
    Coordinates the complete Phase 1 paper processing flow.

    Flow:

        raw paper
            ↓
        normalize
            ↓
        validate
            ↓
        deduplicate identity
            ↓
        resolve
            ↓
        confidence
            ↓
        canonical paper
    """

    def __init__(
        self,
        normalizer: PaperNormalizer | None = None,
        validator: PaperValidator | None = None,
        deduplicator: PaperDeduplicator | None = None,
        resolver: PaperResolver | None = None,
        confidence_scorer: PaperConfidenceScorer | None = None,
    ) -> None:
        self.normalizer = (
            normalizer
            or PaperNormalizer()
        )

        self.validator = (
            validator
            or PaperValidator()
        )

        self.deduplicator = (
            deduplicator
            or PaperDeduplicator()
        )

        self.resolver = (
            resolver
            or PaperResolver()
        )

        self.confidence_scorer = (
            confidence_scorer
            or PaperConfidenceScorer()
        )

    def process(
        self,
        paper: dict[str, Any],
    ) -> PaperProcessingResult:
        normalized = self.normalizer.normalize(
            paper
        )

        self.validator.validate(
            normalized
        )

        identity_key = (
            self.deduplicator.get_identity_key(
                normalized
            )
        )

        resolved = self.resolver.resolve(
            normalized
        )

        scored = self.confidence_scorer.calculate(
            resolved
        )

        return PaperProcessingResult(
            paper=scored,
            identity_key=identity_key,
            confidence_score=scored[
                "confidence_score"
            ],
            confidence_level=scored[
                "confidence_level"
            ],
        )

    def process_many(
        self,
        papers: list[dict[str, Any]],
    ) -> list[PaperProcessingResult]:
        results: list[PaperProcessingResult] = []

        seen: set[str] = set()

        for paper in papers:
            result = self.process(paper)

            if result.identity_key in seen:
                continue

            seen.add(result.identity_key)
            results.append(result)

        return results