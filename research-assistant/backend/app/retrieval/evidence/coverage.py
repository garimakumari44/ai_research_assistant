"""
Evidence coverage calculation.

Coverage estimates how well the retrieved evidence represents the query.

This is deliberately lightweight at the retrieval layer. More advanced
semantic coverage can later be implemented using embeddings or an LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .scorer import EvidenceScorer


@dataclass(slots=True)
class EvidenceCoverage:
    """Coverage information for a retrieval result set."""

    score: float
    matched_terms: list[str]
    missing_terms: list[str]
    evidence_count: int

    @property
    def is_sufficient(self) -> bool:
        """Whether the evidence appears sufficiently covered."""

        return self.score >= 0.60 and self.evidence_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "matched_terms": self.matched_terms,
            "missing_terms": self.missing_terms,
            "evidence_count": self.evidence_count,
            "is_sufficient": self.is_sufficient,
        }


class EvidenceCoverageCalculator:
    """
    Calculates query-to-evidence coverage.

    The implementation uses important query terms and checks whether they
    appear across the retrieved evidence. This provides a deterministic
    baseline without introducing another model dependency.
    """

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    def __init__(
        self,
        *,
        min_term_length: int = 3,
        scorer: EvidenceScorer | None = None,
    ) -> None:
        self.min_term_length = min_term_length
        self.scorer = scorer or EvidenceScorer()

    def calculate(
        self,
        query: str,
        evidence: Sequence[Any] | Iterable[Any],
    ) -> EvidenceCoverage:
        """
        Calculate coverage of retrieved evidence against a query.
        """

        results = list(evidence)

        query_terms = self._extract_terms(query)

        if not query_terms:
            return EvidenceCoverage(
                score=1.0 if results else 0.0,
                matched_terms=[],
                missing_terms=[],
                evidence_count=len(results),
            )

        evidence_text = " ".join(
            self._extract_text(item)
            for item in results
        ).lower()

        matched: list[str] = []
        missing: list[str] = []

        for term in query_terms:
            if self._term_present(term, evidence_text):
                matched.append(term)
            else:
                missing.append(term)

        lexical_score = len(matched) / len(query_terms)

        quality_score = self._quality_score(results)

        final_score = (
            lexical_score * 0.70
            + quality_score * 0.30
        )

        return EvidenceCoverage(
            score=min(max(final_score, 0.0), 1.0),
            matched_terms=matched,
            missing_terms=missing,
            evidence_count=len(results),
        )

    def _extract_terms(self, query: str) -> list[str]:
        """Extract meaningful terms from the query."""

        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", query.lower())

        return list(
            dict.fromkeys(
                token
                for token in tokens
                if len(token) >= self.min_term_length
                and token not in self.STOP_WORDS
            )
        )

    def _extract_text(self, result: Any) -> str:
        """Extract text from a retrieval result."""

        for name in (
            "content",
            "context",
            "text",
            "chunk_text",
            "document_text",
        ):
            value = self._get_value(result, name)

            if value:
                return str(value)

        return ""

    def _quality_score(self, results: Sequence[Any]) -> float:
        """Calculate average evidence quality."""

        if not results:
            return 0.0

        scores = [
            self.scorer.score(result).score
            for result in results
        ]

        return sum(scores) / len(scores)

    @staticmethod
    def _term_present(term: str, text: str) -> bool:
        """
        Check whether a term appears as a complete token.

        Hyphenated identifiers are handled reasonably while avoiding simple
        substring false positives.
        """

        pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"

        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    @staticmethod
    def _get_value(result: Any, name: str) -> Any:
        if isinstance(result, Mapping):
            return result.get(name)

        return getattr(result, name, None)