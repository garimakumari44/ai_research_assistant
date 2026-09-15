from __future__ import annotations

from dataclasses import dataclass
import re

from app.retrieval.models import RetrievalDecision, RetrievalMode


@dataclass(frozen=True)
class QueryRouterConfig:
    """
    Configuration for low-level retrieval routing.
    """

    dense_threshold: float = 0.60
    sparse_threshold: float = 0.75

    # Very short keyword-heavy queries are usually better served
    # by sparse retrieval.
    short_query_terms: int = 4

    # Queries containing these patterns often benefit from semantic
    # retrieval.
    semantic_patterns: tuple[str, ...] = (
        r"\bwhy\b",
        r"\bhow\b",
        r"\bexplain\b",
        r"\bcompare\b",
        r"\bdifference\b",
        r"\bimpact\b",
        r"\brelationship\b",
        r"\bmechanism\b",
        r"\barchitecture\b",
        r"\bapproach\b",
    )


class QueryRouter:
    """
    Select the low-level retrieval mode.

    Modes:

        DENSE
        BM25
        HYBRID

    This router is intentionally lightweight. It does not perform
    retrieval and does not depend on a vector database.

    Adaptive RAG may later override this decision at a higher layer.
    """

    def __init__(
        self,
        config: QueryRouterConfig | None = None,
    ) -> None:
        self.config = (
            config
            or QueryRouterConfig()
        )

    def decide(
        self,
        query: str,
    ) -> RetrievalDecision:
        """
        Determine the preferred retrieval mode.
        """

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "query must be a string"
            )

        query = " ".join(
            query.strip().split()
        )

        if not query:
            return RetrievalDecision(
                mode=RetrievalMode.HYBRID,
                query_type="empty",
                confidence=1.0,
                reason="Empty query; using hybrid fallback.",
            )

        tokens = self._tokenize(
            query
        )

        semantic_score = self._semantic_score(
            query
        )

        keyword_score = self._keyword_score(
            query,
            tokens,
        )

        # ----------------------------------------------------------
        # Strong semantic signal
        # ----------------------------------------------------------

        if semantic_score >= self.config.dense_threshold:
            return RetrievalDecision(
                mode=RetrievalMode.DENSE,
                query_type="semantic",
                confidence=min(
                    semantic_score,
                    1.0,
                ),
                reason=(
                    "Query contains strong semantic/analytical "
                    "language."
                ),
            )

        # ----------------------------------------------------------
        # Short keyword-heavy query
        # ----------------------------------------------------------

        if (
            len(tokens)
            <= self.config.short_query_terms
            and keyword_score
            >= self.config.sparse_threshold
        ):
            return RetrievalDecision(
                mode=RetrievalMode.BM25,
                query_type="keyword",
                confidence=min(
                    keyword_score,
                    1.0,
                ),
                reason=(
                    "Short query with strong lexical/keyword "
                    "characteristics."
                ),
            )

        # ----------------------------------------------------------
        # Mixed signals
        # ----------------------------------------------------------

        return RetrievalDecision(
            mode=RetrievalMode.HYBRID,
            query_type="hybrid",
            confidence=max(
                semantic_score,
                keyword_score,
                0.5,
            ),
            reason=(
                "Query contains mixed semantic and lexical "
                "signals; using hybrid retrieval."
            ),
        )

    # ==================================================================
    # TOKENIZATION
    # ==================================================================

    @staticmethod
    def _tokenize(
        query: str,
    ) -> list[str]:
        return re.findall(
            r"\b[\w-]+\b",
            query.lower(),
        )

    # ==================================================================
    # SEMANTIC SCORING
    # ==================================================================

    def _semantic_score(
        self,
        query: str,
    ) -> float:
        query_lower = query.lower()

        matches = sum(
            1
            for pattern in self.config.semantic_patterns
            if re.search(
                pattern,
                query_lower,
            )
        )

        if matches == 0:
            return 0.0

        # Saturating score.
        return min(
            1.0,
            0.45
            + (
                0.12
                * matches
            ),
        )

    # ==================================================================
    # KEYWORD SCORING
    # ==================================================================

    @staticmethod
    def _keyword_score(
        query: str,
        tokens: list[str],
    ) -> float:
        if not tokens:
            return 0.0

        score = 0.0

        # Presence of exact identifiers / technical tokens.
        identifier_tokens = sum(
            1
            for token in tokens
            if (
                any(
                    character.isdigit()
                    for character in token
                )
                or "-" in token
                or "_" in token
            )
        )

        if identifier_tokens:
            score += min(
                0.45,
                identifier_tokens
                * 0.15,
            )

        # Quoted expressions indicate lexical importance.
        if (
            '"' in query
            or "'" in query
        ):
            score += 0.25

        # Very short queries tend to be lexical.
        if len(tokens) <= 3:
            score += 0.30
        elif len(tokens) <= 5:
            score += 0.15

        return min(
            score,
            1.0,
        )


__all__ = [
    "QueryRouter",
    "QueryRouterConfig",
]