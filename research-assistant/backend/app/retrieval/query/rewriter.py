
"""
Query rewriting for retrieval.

The QueryRewriter converts analyzed queries into retrieval-friendly
queries without changing the user's original intent.

This implementation is deterministic and does not require an LLM.

The planner owns the query budget. Therefore the rewriter accepts
max_queries rather than hard-coding an execution budget.
"""

from __future__ import annotations

from app.retrieval.models import (
    QueryAnalysis,
    QueryRewrite,
)


class QueryRewriter:
    """
    Retrieval-oriented deterministic query rewriter.

    Responsibilities:

        - preserve the original intent
        - produce a compact retrieval query
        - expand known technical abbreviations
        - produce complementary search queries
        - respect the planner-provided query budget
    """

    TERM_EXPANSIONS: dict[str, list[str]] = {
        "rag": [
            "retrieval augmented generation",
            "retrieval-augmented generation",
        ],
        "llm": [
            "large language model",
            "large language models",
        ],
        "nlp": [
            "natural language processing",
        ],
        "ir": [
            "information retrieval",
        ],
        "ml": [
            "machine learning",
        ],
        "dl": [
            "deep learning",
        ],
        "transformer": [
            "transformer model",
            "transformer architecture",
        ],
        "embedding": [
            "vector embedding",
            "text embedding",
        ],
        "reranking": [
            "reranking",
            "re-ranking",
        ],
        "reranker": [
            "reranking model",
            "re-ranking model",
        ],
        "bm25": [
            "BM25",
            "sparse retrieval",
        ],
        "vector search": [
            "dense retrieval",
            "vector retrieval",
        ],
    }

    DEFAULT_MAX_QUERIES = 3

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def rewrite(
        self,
        analysis: QueryAnalysis,
        max_queries: int | None = None,
    ) -> QueryRewrite:
        """
        Rewrite an analyzed query.

        Args:
            analysis:
                Canonical QueryAnalysis.

            max_queries:
                Maximum number of generated search queries.

                This should normally come from the Adaptive RAG
                retrieval plan.

        Returns:
            QueryRewrite
        """

        if max_queries is None:
            max_queries = self.DEFAULT_MAX_QUERIES

        if max_queries < 1:
            raise ValueError(
                "max_queries must be greater than zero"
            )

        expanded_terms = self._expand_terms(
            analysis.keywords
        )

        rewritten_query = self._build_rewritten_query(
            analysis,
            expanded_terms,
        )

        search_queries = self._build_search_queries(
            analysis,
            expanded_terms,
            max_queries=max_queries,
        )

        return QueryRewrite(
            original_query=analysis.original_query,
            rewritten_query=rewritten_query,
            search_queries=search_queries,
            keywords=list(analysis.keywords),
            expanded_terms=expanded_terms,
            metadata={
                "query_intent": analysis.intent.value,
                "query_type": analysis.query_type.value,
                "complexity": analysis.complexity.value,
            },
        )

    # ==================================================================
    # TERM EXPANSION
    # ==================================================================

    def _expand_terms(
        self,
        keywords: list[str],
    ) -> list[str]:
        """
        Expand known research abbreviations and terminology.
        """

        expansions: list[str] = []
        seen: set[str] = set()

        for keyword in keywords:
            normalized = keyword.casefold().strip()

            candidates = self.TERM_EXPANSIONS.get(
                normalized,
                [],
            )

            for candidate in candidates:
                key = candidate.casefold().strip()

                if not key or key in seen:
                    continue

                seen.add(key)
                expansions.append(candidate)

        return expansions

    # ==================================================================
    # REWRITTEN QUERY
    # ==================================================================

    def _build_rewritten_query(
        self,
        analysis: QueryAnalysis,
        expanded_terms: list[str],
    ) -> str:
        """
        Build a concise retrieval query.

        Preference order:

            1. important keywords
            2. expanded terminology
            3. quoted phrases
            4. normalized original query as fallback
        """

        parts: list[str] = []

        parts.extend(
            analysis.keywords
        )

        parts.extend(
            expanded_terms
        )

        parts.extend(
            analysis.phrases
        )

        parts = self._deduplicate(
            parts
        )

        if not parts:
            return analysis.normalized_query

        return " ".join(parts)

    # ==================================================================
    # SEARCH QUERIES
    # ==================================================================

    def _build_search_queries(
        self,
        analysis: QueryAnalysis,
        expanded_terms: list[str],
        max_queries: int,
    ) -> list[str]:
        """
        Generate complementary search queries.

        Candidate order:

            1. Original semantic query.
            2. Keyword-focused query.
            3. Expanded terminology query.

        The caller controls the maximum number of queries.
        """

        candidates: list[str] = []

        # --------------------------------------------------------------
        # Candidate 1: original semantic query
        # --------------------------------------------------------------

        self._append_unique(
            candidates,
            analysis.normalized_query,
        )

        # --------------------------------------------------------------
        # Candidate 2: keyword query
        # --------------------------------------------------------------

        keyword_query = " ".join(
            analysis.keywords
        )

        self._append_unique(
            candidates,
            keyword_query,
        )

        # --------------------------------------------------------------
        # Candidate 3: expanded query
        # --------------------------------------------------------------

        expanded_query = " ".join(
            self._deduplicate(
                [
                    *analysis.keywords,
                    *expanded_terms,
                ]
            )
        )

        self._append_unique(
            candidates,
            expanded_query,
        )

        # --------------------------------------------------------------
        # Candidate 4: phrase-focused query
        # --------------------------------------------------------------

        phrase_query = " ".join(
            self._deduplicate(
                [
                    *analysis.phrases,
                    *analysis.keywords,
                ]
            )
        )

        self._append_unique(
            candidates,
            phrase_query,
        )

        return candidates[:max_queries]

    # ==================================================================
    # UTILITIES
    # ==================================================================

    @staticmethod
    def _deduplicate(
        values: list[str],
    ) -> list[str]:
        """
        Deduplicate strings while preserving order.
        """

        seen: set[str] = set()
        result: list[str] = []

        for value in values:
            normalized = value.casefold().strip()

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(value.strip())

        return result

    @staticmethod
    def _append_unique(
        values: list[str],
        value: str,
    ) -> None:
        """
        Append a query only if it is non-empty and unique.
        """

        normalized = value.casefold().strip()

        if not normalized:
            return

        existing = {
            item.casefold().strip()
            for item in values
        }

        if normalized not in existing:
            values.append(value.strip())


__all__ = [
    "QueryRewriter",
    "QueryRewrite",
]

