"""
Default reranker implementation.

This implementation provides a lightweight lexical relevance
reranker that works without an external model.

It is intentionally designed as a production-safe fallback.

A model-based reranker can later replace this implementation while
keeping the same BaseReranker interface.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Sequence

from app.retrieval.reranking.base import (
    BaseReranker,
    RerankCandidate,
    RerankResult,
)


class DefaultReranker(BaseReranker):
    """
    Lightweight lexical reranker.

    The score combines:

        1. Query-term coverage
        2. Term-frequency similarity
        3. Exact phrase matching
        4. Title/metadata matches
        5. Original retrieval score

    This is not intended to replace a neural cross-encoder. It gives
    the retrieval pipeline a deterministic reranking stage that works
    immediately and can later be upgraded.
    """

    name = "default"

    TOKEN_PATTERN = re.compile(
        r"\b[a-zA-Z0-9][a-zA-Z0-9_\-./]*\b"
    )

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
        lexical_weight: float = 0.55,
        phrase_weight: float = 0.15,
        metadata_weight: float = 0.10,
        original_score_weight: float = 0.20,
    ) -> None:
        """
        Initialize the reranker.

        The weights are normalized automatically if their sum is not
        exactly 1.0.
        """

        total = (
            lexical_weight
            + phrase_weight
            + metadata_weight
            + original_score_weight
        )

        if total <= 0:
            raise ValueError(
                "Reranker weights must sum to a positive value."
            )

        self.lexical_weight = lexical_weight / total
        self.phrase_weight = phrase_weight / total
        self.metadata_weight = metadata_weight / total
        self.original_score_weight = (
            original_score_weight / total
        )

    async def rerank(
        self,
        query: str,
        candidates: Sequence[RerankCandidate],
        *,
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """
        Rerank candidates against the supplied query.
        """

        prepared = self._prepare_candidates(
            candidates
        )

        if not prepared:
            return []

        normalized_query = self._normalize(query)

        query_tokens = self._tokenize(
            normalized_query
        )

        query_terms = [
            token
            for token in query_tokens
            if token not in self.STOP_WORDS
        ]

        query_counter = Counter(query_terms)

        results: list[RerankResult] = []

        for candidate in prepared:
            content = candidate.content or ""

            normalized_content = self._normalize(
                content
            )

            content_tokens = self._tokenize(
                normalized_content
            )

            content_counter = Counter(
                token
                for token in content_tokens
                if token not in self.STOP_WORDS
            )

            lexical_score = self._lexical_score(
                query_counter,
                content_counter,
            )

            phrase_score = self._phrase_score(
                normalized_query,
                normalized_content,
            )

            metadata_score = self._metadata_score(
                query_terms,
                candidate,
            )

            original_score = self._normalize_original_score(
                candidate.original_score
                if candidate.original_score is not None
                else candidate.score
            )

            final_score = (
                self.lexical_weight * lexical_score
                + self.phrase_weight * phrase_score
                + self.metadata_weight * metadata_score
                + self.original_score_weight * original_score
            )

            results.append(
                RerankResult(
                    candidate=candidate,
                    score=round(
                        final_score,
                        6,
                    ),
                    rank=0,
                    original_rank=candidate.original_rank,
                    reason=self._build_reason(
                        lexical_score=lexical_score,
                        phrase_score=phrase_score,
                        metadata_score=metadata_score,
                    ),
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return self._limit_results(
            results,
            top_k,
        )

    def _lexical_score(
        self,
        query_counter: Counter[str],
        document_counter: Counter[str],
    ) -> float:
        """
        Calculate weighted lexical overlap.

        A query term contributes more when it appears in the document,
        while repeated occurrences have diminishing returns.
        """

        if not query_counter:
            return 0.0

        matched_weight = 0.0
        total_weight = float(
            sum(query_counter.values())
        )

        for term, query_frequency in query_counter.items():
            if term not in document_counter:
                continue

            document_frequency = document_counter[
                term
            ]

            occurrence_factor = min(
                1.0,
                math.log1p(
                    document_frequency
                )
                / math.log(2.0),
            )

            contribution = min(
                1.0,
                query_frequency
                * occurrence_factor,
            )

            matched_weight += contribution

        coverage = matched_weight / total_weight

        cosine_similarity = self._cosine_similarity(
            query_counter,
            document_counter,
        )

        return min(
            1.0,
            (0.65 * coverage)
            + (0.35 * cosine_similarity),
        )

    @staticmethod
    def _cosine_similarity(
        first: Counter[str],
        second: Counter[str],
    ) -> float:
        """
        Calculate cosine similarity between two token vectors.
        """

        if not first or not second:
            return 0.0

        shared_terms = set(first) & set(second)

        if not shared_terms:
            return 0.0

        dot_product = sum(
            first[token] * second[token]
            for token in shared_terms
        )

        first_norm = math.sqrt(
            sum(
                value * value
                for value in first.values()
            )
        )

        second_norm = math.sqrt(
            sum(
                value * value
                for value in second.values()
            )
        )

        if first_norm == 0 or second_norm == 0:
            return 0.0

        return dot_product / (
            first_norm * second_norm
        )

    @staticmethod
    def _phrase_score(
        query: str,
        content: str,
    ) -> float:
        """
        Score exact phrase overlap.

        Full-query matching receives the highest score.
        """

        query = query.strip()

        if not query or not content:
            return 0.0

        if query in content:
            return 1.0

        query_terms = query.split()

        if len(query_terms) < 2:
            return 0.0

        phrase_length = 2

        matching_phrases = 0
        total_phrases = max(
            1,
            len(query_terms) - phrase_length + 1,
        )

        for index in range(
            len(query_terms) - phrase_length + 1
        ):
            phrase = " ".join(
                query_terms[
                    index : index + phrase_length
                ]
            )

            if phrase in content:
                matching_phrases += 1

        return min(
            1.0,
            matching_phrases / total_phrases,
        )

    def _metadata_score(
        self,
        query_terms: list[str],
        candidate: RerankCandidate,
    ) -> float:
        """
        Check whether query terms appear in useful metadata fields.

        Metadata can include fields such as:

            title
            abstract
            authors
            topics
            venue
        """

        if not query_terms:
            return 0.0

        metadata = candidate.metadata or {}

        searchable_values: list[str] = []

        for key in (
            "title",
            "abstract",
            "authors",
            "author",
            "topics",
            "topic",
            "venue",
            "keywords",
            "paper_title",
        ):
            value = metadata.get(key)

            if value is None:
                continue

            if isinstance(value, list):
                searchable_values.extend(
                    str(item)
                    for item in value
                )
            else:
                searchable_values.append(
                    str(value)
                )

        if candidate.document_id:
            searchable_values.append(
                candidate.document_id
            )

        metadata_text = self._normalize(
            " ".join(searchable_values)
        )

        if not metadata_text:
            return 0.0

        metadata_tokens = set(
            self._tokenize(
                metadata_text
            )
        )

        matched = sum(
            1
            for term in query_terms
            if term in metadata_tokens
        )

        return min(
            1.0,
            matched / len(query_terms),
        )

    @staticmethod
    def _normalize_original_score(
        score: float | None,
    ) -> float:
        """
        Normalize upstream retrieval scores.

        Retrieval systems may return negative or arbitrarily scaled
        values, so we clamp the score into [0, 1].
        """

        if score is None:
            return 0.0

        try:
            value = float(score)
        except (TypeError, ValueError):
            return 0.0

        if not math.isfinite(value):
            return 0.0

        return max(
            0.0,
            min(1.0, value),
        )

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize text for lexical comparison.
        """

        return " ".join(
            text.lower().strip().split()
        )

    def _tokenize(
        self,
        text: str,
    ) -> list[str]:
        """
        Tokenize normalized text.
        """

        return [
            token.lower()
            for token in self.TOKEN_PATTERN.findall(
                text
            )
        ]

    @staticmethod
    def _build_reason(
        *,
        lexical_score: float,
        phrase_score: float,
        metadata_score: float,
    ) -> str:
        """
        Produce a compact explanation for debugging and observability.
        """

        reasons: list[str] = []

        if lexical_score >= 0.70:
            reasons.append(
                "strong lexical match"
            )
        elif lexical_score >= 0.40:
            reasons.append(
                "moderate lexical match"
            )
        elif lexical_score > 0:
            reasons.append(
                "weak lexical match"
            )

        if phrase_score >= 0.50:
            reasons.append(
                "phrase overlap"
            )

        if metadata_score >= 0.50:
            reasons.append(
                "metadata match"
            )

        if not reasons:
            return "low direct relevance signals"

        return ", ".join(reasons)