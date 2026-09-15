
"""
Deterministic query classification for the retrieval pipeline.

The classifier determines the semantic intent of a query.

It does NOT decide:

    - dense vs BM25 vs hybrid
    - Adaptive RAG strategy
    - retrieval budget

Those decisions belong to downstream routing/planning components.
"""

from __future__ import annotations

import re

from app.retrieval.models import (
    QueryClassification,
    QueryIntent,
)


class QueryClassifier:
    """
    Lightweight deterministic query classifier.

    Advantages:

        - deterministic
        - fast
        - inexpensive
        - easy to test
        - no LLM dependency

    The classifier can later be replaced or augmented by an ML/LLM
    classifier without changing the QueryAnalysis contract.
    """

    COMPARATIVE_PATTERNS = (
        r"\bcompare\b",
        r"\bcomparison\b",
        r"\bcompar(e|ing)\b",
        r"\bversus\b",
        r"\bvs\.?\b",
        r"\bdifference between\b",
        r"\bdifferences between\b",
        r"\bbetter than\b",
        r"\bsimilarities\b",
        r"\bsimilar to\b",
    )

    DEFINITIONAL_PATTERNS = (
        r"^what is\b",
        r"^what are\b",
        r"\bdefine\b",
        r"\bdefinition of\b",
        r"\bmeaning of\b",
        r"\bwhat does .* mean\b",
    )

    METHOD_PATTERNS = (
        r"\bhow does\b",
        r"\bhow do\b",
        r"\bhow is\b",
        r"\bhow are\b",
        r"\bmethod\b",
        r"\bmethodology\b",
        r"\bapproach\b",
        r"\balgorithm\b",
        r"\barchitecture\b",
        r"\btechnique\b",
        r"\bimplementation\b",
    )

    DATASET_PATTERNS = (
        r"\bdataset\b",
        r"\bdatasets\b",
        r"\bbenchmark\b",
        r"\bbenchmarks\b",
        r"\bcorpus\b",
        r"\bdata set\b",
        r"\btraining data\b",
        r"\bevaluation data\b",
    )

    LITERATURE_PATTERNS = (
        r"\bliterature\b",
        r"\bresearch papers?\b",
        r"\bstate of the art\b",
        r"\bsurvey\b",
        r"\breview\b",
        r"\bprior work\b",
        r"\brelated work\b",
        r"\bexisting research\b",
        r"\brecent research\b",
        r"\bpublished work\b",
    )

    EXPLANATORY_PATTERNS = (
        r"\bexplain\b",
        r"\bwhy\b",
        r"\breason\b",
        r"\breasons\b",
        r"\bcauses?\b",
        r"\bimpact\b",
        r"\beffect\b",
        r"\beffects\b",
        r"\bimplications?\b",
    )

    MULTI_HOP_PATTERNS = (
        r"\brelationship between\b",
        r"\brelate\b",
        r"\bconnected to\b",
        r"\bconnection between\b",
        r"\bhow .* affects .* and\b",
        r"\bfrom .* to .*\b",
        r"\bwhy .* leads to\b",
    )

    def classify(
        self,
        query: str,
    ) -> QueryClassification:
        """
        Classify a raw query.
        """

        if not isinstance(query, str):
            raise TypeError("query must be a string")

        normalized = self._normalize(query)

        if not normalized:
            return QueryClassification(
                intent=QueryIntent.GENERAL,
                confidence=0.0,
                signals=[],
                requires_multiple_documents=False,
                requires_broad_search=False,
                requires_multi_hop=False,
            )

        candidates: list[
            tuple[QueryIntent, list[str]]
        ] = [
            (
                QueryIntent.MULTI_HOP,
                self._match_patterns(
                    normalized,
                    self.MULTI_HOP_PATTERNS,
                ),
            ),
            (
                QueryIntent.COMPARATIVE,
                self._match_patterns(
                    normalized,
                    self.COMPARATIVE_PATTERNS,
                ),
            ),
            (
                QueryIntent.DEFINITIONAL,
                self._match_patterns(
                    normalized,
                    self.DEFINITIONAL_PATTERNS,
                ),
            ),
            (
                QueryIntent.METHOD,
                self._match_patterns(
                    normalized,
                    self.METHOD_PATTERNS,
                ),
            ),
            (
                QueryIntent.DATASET,
                self._match_patterns(
                    normalized,
                    self.DATASET_PATTERNS,
                ),
            ),
            (
                QueryIntent.LITERATURE,
                self._match_patterns(
                    normalized,
                    self.LITERATURE_PATTERNS,
                ),
            ),
            (
                QueryIntent.EXPLANATORY,
                self._match_patterns(
                    normalized,
                    self.EXPLANATORY_PATTERNS,
                ),
            ),
        ]

        matched = [
            (intent, signals)
            for intent, signals in candidates
            if signals
        ]

        if not matched:
            return QueryClassification(
                intent=QueryIntent.FACTUAL,
                confidence=0.55,
                signals=[],
                requires_multiple_documents=False,
                requires_broad_search=False,
                requires_multi_hop=False,
            )

        # Deterministic ranking:
        #
        # 1. Number of matching signals.
        # 2. Intent priority for ties.
        #
        # This avoids arbitrary dictionary/order behaviour.

        priority = {
            QueryIntent.MULTI_HOP: 7,
            QueryIntent.COMPARATIVE: 6,
            QueryIntent.LITERATURE: 5,
            QueryIntent.METHOD: 4,
            QueryIntent.DATASET: 3,
            QueryIntent.DEFINITIONAL: 2,
            QueryIntent.EXPLANATORY: 1,
        }

        matched.sort(
            key=lambda item: (
                len(item[1]),
                priority.get(item[0], 0),
            ),
            reverse=True,
        )

        intent, signals = matched[0]

        confidence = min(
            0.95,
            0.60 + (0.08 * len(signals)),
        )

        requires_multiple_documents = intent in {
            QueryIntent.COMPARATIVE,
            QueryIntent.LITERATURE,
            QueryIntent.MULTI_HOP,
        }

        requires_broad_search = intent in {
            QueryIntent.COMPARATIVE,
            QueryIntent.LITERATURE,
        }

        requires_multi_hop = intent == QueryIntent.MULTI_HOP

        return QueryClassification(
            intent=intent,
            confidence=confidence,
            signals=signals,
            requires_multiple_documents=(
                requires_multiple_documents
            ),
            requires_broad_search=(
                requires_broad_search
            ),
            requires_multi_hop=(
                requires_multi_hop
            ),
        )

    @staticmethod
    def _normalize(query: str) -> str:
        """
        Normalize whitespace without changing semantic content.
        """

        return " ".join(
            query.lower().strip().split()
        )

    @staticmethod
    def _match_patterns(
        query: str,
        patterns: tuple[str, ...],
    ) -> list[str]:
        """
        Return all patterns that match the query.
        """

        matches: list[str] = []

        for pattern in patterns:
            if re.search(
                pattern,
                query,
                flags=re.IGNORECASE,
            ):
                matches.append(pattern)

        return matches


__all__ = [
    "QueryClassifier",
]

