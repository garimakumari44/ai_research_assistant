
"""
Query analysis for the retrieval pipeline.

QueryAnalyzer converts a raw user query into the canonical
QueryAnalysis representation.

Pipeline:

    raw query
        ↓
    normalization
        ↓
    semantic classification
        ↓
    lexical extraction
        ↓
    phrase extraction
        ↓
    filter extraction
        ↓
    QueryAnalysis
"""

from __future__ import annotations

import re
from typing import Any

from app.retrieval.query.classifier import QueryClassifier
from app.retrieval.models import (
    QueryAnalysis,
    QueryComplexity,
    QueryIntent,
    QueryType,
)


class QueryAnalyzer:
    """
    Deterministic retrieval query analyzer.

    Responsibilities:

        - normalize query text
        - classify semantic intent
        - determine retrieval representation
        - extract terms
        - extract keywords
        - extract quoted phrases
        - extract lightweight filters
        - identify question structure
        - estimate query complexity
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

    # ------------------------------------------------------------------
    # Common retrieval indicators
    # ------------------------------------------------------------------

    KEYWORD_INDICATORS = {
        "exact",
        "keyword",
        "identifier",
        "id",
        "code",
        "title",
        "author",
        "dataset",
        "paper",
    }

    SEMANTIC_INDICATORS = {
        "explain",
        "why",
        "relationship",
        "meaning",
        "concept",
        "implication",
        "impact",
    }

    def __init__(
        self,
        classifier: QueryClassifier | None = None,
    ) -> None:
        self.classifier = classifier or QueryClassifier()

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def analyze(
        self,
        query: str,
    ) -> QueryAnalysis:
        """
        Analyze a raw user query.
        """

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string"
            )

        original_query = query.strip()

        if not original_query:
            raise ValueError(
                "query cannot be empty"
            )

        normalized_query = self.normalize(
            original_query
        )

        classification = self.classifier.classify(
            normalized_query
        )

        terms = self._extract_terms(
            normalized_query
        )

        keywords = self._extract_keywords(
            terms
        )

        phrases = self._extract_phrases(
            original_query
        )

        filters = self._extract_filters(
            original_query
        )

        query_type = self._infer_query_type(
            normalized_query,
            classification.intent,
            keywords,
            phrases,
        )

        complexity = self._estimate_complexity(
            normalized_query,
            classification.intent,
            classification.requires_multiple_documents,
            classification.requires_multi_hop,
        )

        requires_reranking = (
            classification.requires_multiple_documents
            or classification.requires_broad_search
            or classification.requires_multi_hop
        )

        requires_multiple_queries = (
            classification.requires_broad_search
            or classification.requires_multi_hop
        )

        return QueryAnalysis(
            original_query=original_query,
            normalized_query=normalized_query,
            intent=classification.intent,
            complexity=complexity,
            query_type=query_type,
            classification_confidence=(
                classification.confidence
            ),
            terms=terms,
            keywords=keywords,
            phrases=phrases,
            filters=filters,
            requires_retrieval=True,
            requires_multiple_documents=(
                classification.requires_multiple_documents
            ),
            requires_broad_search=(
                classification.requires_broad_search
            ),
            requires_multi_hop=(
                classification.requires_multi_hop
            ),
            requires_reranking=(
                requires_reranking
            ),
            requires_multiple_queries=(
                requires_multiple_queries
            ),
            is_question=self._is_question(
                original_query
            ),
            metadata={
                "classifier_signals": (
                    classification.signals
                ),
            },
        )

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def normalize(
        query: str,
    ) -> str:
        """
        Normalize whitespace and case.

        We deliberately do not aggressively strip punctuation because
        punctuation can be meaningful for technical identifiers,
        version numbers, paths, APIs, and mathematical notation.
        """

        normalized = query.strip().lower()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized

    # ==================================================================
    # TERM EXTRACTION
    # ==================================================================

    def _extract_terms(
        self,
        query: str,
    ) -> list[str]:
        """
        Extract meaningful lexical terms.

        Unicode-aware word extraction is used instead of restricting
        tokens to ASCII characters.
        """

        tokens = re.findall(
            r"[^\W_]+(?:[-./][^\W_]+)*",
            query,
            flags=re.UNICODE,
        )

        return [
            token
            for token in tokens
            if token.casefold() not in self.STOP_WORDS
            and len(token) > 1
        ]

    def _extract_keywords(
        self,
        terms: list[str],
    ) -> list[str]:
        """
        Deduplicate terms while preserving order.
        """

        seen: set[str] = set()
        keywords: list[str] = []

        for term in terms:
            normalized = term.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            keywords.append(term)

        return keywords

    # ==================================================================
    # PHRASE EXTRACTION
    # ==================================================================

    @staticmethod
    def _extract_phrases(
        query: str,
    ) -> list[str]:
        """
        Extract explicitly quoted phrases.

        Example:

            "retrieval augmented generation"
        """

        phrases = re.findall(
            r'"([^"]+)"',
            query,
        )

        return [
            phrase.strip()
            for phrase in phrases
            if phrase.strip()
        ]

    # ==================================================================
    # FILTER EXTRACTION
    # ==================================================================

    @staticmethod
    def _extract_filters(
        query: str,
    ) -> dict[str, Any]:
        """
        Extract lightweight retrieval filters.

        Supported syntax includes:

            year:2024
            year:2020-2024
            author:"John Smith"
            topic:RAG
            source:arxiv
            venue:"NeurIPS"
            document:abc123
            paper:abc123

        The resulting keys are aligned with the canonical retrieval
        filter vocabulary as much as possible.
        """

        filters: dict[str, Any] = {}

        pattern = re.compile(
            r"""
            (?P<key>
                year|
                author|
                topic|
                source|
                venue|
                document|
                paper|
                source_type
            )
            :
            (?P<value>
                "[^"]+"
                |
                \S+
            )
            """,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        for match in pattern.finditer(query):
            raw_key = match.group("key")
            raw_value = match.group("value")

            key = raw_key.lower().strip()
            value = raw_value.strip().strip('"')

            if not value:
                continue

            # ----------------------------------------------------------
            # Year
            # ----------------------------------------------------------

            if key == "year":
                year_range = re.fullmatch(
                    r"(\d{4})-(\d{4})",
                    value,
                )

                if year_range:
                    filters["year_from"] = int(
                        year_range.group(1)
                    )
                    filters["year_to"] = int(
                        year_range.group(2)
                    )
                    continue

                try:
                    year = int(value)

                    filters["year_from"] = year
                    filters["year_to"] = year

                except ValueError:
                    filters["year"] = value

                continue

            # ----------------------------------------------------------
            # Canonical identifier mappings
            # ----------------------------------------------------------

            if key == "paper":
                filters["paper_id"] = value
                continue

            if key == "document":
                filters["document_id"] = value
                continue

            if key == "source_type":
                filters["source_type"] = value
                continue

            # ----------------------------------------------------------
            # Normal metadata filters
            # ----------------------------------------------------------

            filters[key] = value

        return filters

    # ==================================================================
    # RETRIEVAL TYPE
    # ==================================================================

    def _infer_query_type(
        self,
        query: str,
        intent: QueryIntent,
        keywords: list[str],
        phrases: list[str],
    ) -> QueryType:
        """
        Infer the low-level retrieval representation.

        This is intentionally independent from semantic intent.
        """

        tokens = {
            keyword.casefold()
            for keyword in keywords
        }

        has_keyword_signal = bool(
            tokens.intersection(
                self.KEYWORD_INDICATORS
            )
        )

        has_semantic_signal = bool(
            tokens.intersection(
                self.SEMANTIC_INDICATORS
            )
        )

        # Explicit quoted phrases benefit from lexical matching,
        # while the surrounding query may still need semantic retrieval.
        has_exact_phrase = bool(phrases)

        if has_keyword_signal and has_semantic_signal:
            return QueryType.HYBRID

        if has_exact_phrase and intent in {
            QueryIntent.FACTUAL,
            QueryIntent.DEFINITIONAL,
        }:
            return QueryType.HYBRID

        if has_keyword_signal:
            return QueryType.KEYWORD

        if has_semantic_signal:
            return QueryType.SEMANTIC

        # Research-heavy queries generally benefit from hybrid search.
        if intent in {
            QueryIntent.COMPARATIVE,
            QueryIntent.LITERATURE,
            QueryIntent.METHOD,
            QueryIntent.MULTI_HOP,
        }:
            return QueryType.HYBRID

        return QueryType.HYBRID

    # ==================================================================
    # COMPLEXITY
    # ==================================================================

    @staticmethod
    def _estimate_complexity(
        query: str,
        intent: QueryIntent,
        requires_multiple_documents: bool,
        requires_multi_hop: bool,
    ) -> QueryComplexity:
        """
        Estimate query complexity using deterministic signals.
        """

        word_count = len(
            query.split()
        )

        if requires_multi_hop:
            return QueryComplexity.HIGH

        if intent in {
            QueryIntent.COMPARATIVE,
            QueryIntent.LITERATURE,
        }:
            return QueryComplexity.HIGH

        if (
            requires_multiple_documents
            or word_count >= 25
        ):
            return QueryComplexity.MEDIUM

        if (
            intent in {
                QueryIntent.METHOD,
                QueryIntent.EXPLANATORY,
                QueryIntent.DATASET,
            }
            and word_count >= 10
        ):
            return QueryComplexity.MEDIUM

        return QueryComplexity.LOW

    # ==================================================================
    # QUESTION DETECTION
    # ==================================================================

    @staticmethod
    def _is_question(
        query: str,
    ) -> bool:
        """
        Determine whether the query is phrased as a question.
        """

        normalized = query.lower().strip()

        if normalized.endswith("?"):
            return True

        question_starters = (
            "what ",
            "why ",
            "how ",
            "when ",
            "where ",
            "which ",
            "who ",
            "can ",
            "could ",
            "does ",
            "do ",
            "is ",
            "are ",
            "will ",
            "would ",
            "should ",
        )

        return normalized.startswith(
            question_starters
        )


__all__ = [
    "QueryAnalyzer",
    "QueryAnalysis",
]

