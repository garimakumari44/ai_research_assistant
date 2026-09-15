from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from .collector import EvidenceItem


@dataclass(frozen=True, slots=True)
class CoverageResult:
    """
    Measures how much of the requested query is represented by evidence.
    """

    score: float

    query_terms: tuple[str, ...]
    covered_terms: tuple[str, ...]
    uncovered_terms: tuple[str, ...]

    evidence_count: int

    @property
    def sufficient(self) -> bool:
        return self.score >= 0.7


class EvidenceCoverageEvaluator:
    """
    Lightweight lexical coverage evaluator.

    This is intentionally not an LLM-based evaluator.

    It answers:

        "Does the retrieved evidence contain the important terms
         required to address the query?"

    It does not answer:

        "Is the evidence factually correct?"
    """

    DEFAULT_STOPWORDS = frozenset(
        {
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
            "of",
            "on",
            "or",
            "that",
            "the",
            "to",
            "what",
            "when",
            "where",
            "which",
            "who",
            "why",
            "with",
        }
    )

    def __init__(
        self,
        *,
        stopwords: Iterable[str] | None = None,
        min_term_length: int = 2,
    ) -> None:
        self.stopwords = frozenset(
            stopwords
            if stopwords is not None
            else self.DEFAULT_STOPWORDS
        )

        self.min_term_length = min_term_length

    def evaluate(
        self,
        query: str,
        evidence: Sequence[EvidenceItem],
    ) -> CoverageResult:
        if not query.strip():
            raise ValueError("query cannot be empty")

        query_terms = self._terms(query)

        if not query_terms:
            return CoverageResult(
                score=0.0,
                query_terms=(),
                covered_terms=(),
                uncovered_terms=(),
                evidence_count=len(evidence),
            )

        corpus = " ".join(
            item.content.lower()
            for item in evidence
        )

        covered = tuple(
            term
            for term in query_terms
            if self._term_present(term, corpus)
        )

        uncovered = tuple(
            term
            for term in query_terms
            if term not in covered
        )

        score = len(covered) / len(query_terms)

        return CoverageResult(
            score=score,
            query_terms=query_terms,
            covered_terms=covered,
            uncovered_terms=uncovered,
            evidence_count=len(evidence),
        )

    def _terms(
        self,
        text: str,
    ) -> tuple[str, ...]:
        tokens = re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
            text.lower(),
        )

        result: list[str] = []

        for token in tokens:
            if len(token) < self.min_term_length:
                continue

            if token in self.stopwords:
                continue

            if token not in result:
                result.append(token)

        return tuple(result)

    @staticmethod
    def _term_present(
        term: str,
        corpus: str,
    ) -> bool:
        pattern = rf"\b{re.escape(term)}\b"

        return re.search(
            pattern,
            corpus,
            flags=re.IGNORECASE,
        ) is not None