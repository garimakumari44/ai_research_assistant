"""
Adaptive RAG planner.

The planner determines how the system should retrieve information
for a given query.

It does NOT execute retrieval.

Responsibilities
----------------
- Analyze query characteristics.
- Select retrieval strategy.
- Configure top-k.
- Decide whether reranking is required.
- Decide whether query expansion is useful.
- Decide whether multi-hop retrieval is required.

Design
------
The planner is deterministic and provider-independent.

It produces:

    query
      ↓
    QueryAnalysis
      ↓
    RetrievalPlan
      ↓
    RetrievalPipeline / RetrievalService
"""

from __future__ import annotations

import re

from .domain_models import (
    AdaptiveRAGConfig,
    QueryAnalysis,
    QueryComplexity,
    QueryIntent,
    RetrievalPlan,
    RetrievalStrategy,
)


class AdaptiveRAGPlanner:
    """
    Generates retrieval plans from query analysis.

    The planner never performs retrieval itself.

    Example:

        planner = AdaptiveRAGPlanner()

        analysis, plan = planner.plan(
            "Compare transformer and RNN architectures"
        )
    """

    # ==================================================================
    # QUERY CLASSIFICATION TERMS
    # ==================================================================

    COMPARISON_TERMS = frozenset(
        {
            "compare",
            "comparison",
            "versus",
            "vs",
            "difference",
            "differences",
            "better",
            "best",
        }
    )

    ANALYTICAL_TERMS = frozenset(
        {
            "why",
            "how",
            "analyze",
            "analysis",
            "explain",
            "evaluate",
            "impact",
            "effect",
            "cause",
            "reason",
        }
    )

    MULTI_HOP_TERMS = (
        "and how",
        "relationship",
        "relationships",
        "connected",
        "connection",
        "connections",
        "based on",
        "according to",
        "then",
        "after",
        "followed by",
        "lead to",
        "leads to",
        "result in",
        "resulting in",
    )

    SUMMARY_TERMS = frozenset(
        {
            "summarize",
            "summarise",
            "summary",
            "overview",
            "key points",
            "main points",
            "give me a summary",
        }
    )

    STOP_WORDS = frozenset(
        {
            "the",
            "a",
            "an",
            "is",
            "are",
            "am",
            "was",
            "were",
            "be",
            "been",
            "being",
            "what",
            "why",
            "how",
            "when",
            "where",
            "who",
            "which",
            "whose",
            "and",
            "or",
            "but",
            "if",
            "then",
            "than",
            "to",
            "of",
            "in",
            "on",
            "for",
            "with",
            "from",
            "by",
            "as",
            "at",
            "into",
            "about",
            "over",
            "under",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "their",
            "there",
            "here",
            "can",
            "could",
            "would",
            "should",
            "do",
            "does",
            "did",
            "using",
            "use",
        }
    )

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def __init__(
        self,
        config: AdaptiveRAGConfig | None = None,
    ) -> None:
        """
        Initialize the planner.

        Args:
            config:
                Adaptive RAG configuration.

        Raises:
            TypeError:
                If config is not an AdaptiveRAGConfig instance.
        """

        if config is not None and not isinstance(
            config,
            AdaptiveRAGConfig,
        ):
            raise TypeError(
                "config must be an AdaptiveRAGConfig instance"
            )

        self.config = config or AdaptiveRAGConfig()

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def analyze_query(
        self,
        query: str,
    ) -> QueryAnalysis:
        """
        Perform lightweight deterministic query analysis.

        This method does not execute retrieval and does not depend
        on any LLM or external provider.

        Args:
            query:
                User's natural-language query.

        Returns:
            QueryAnalysis describing the query.
        """

        normalized = self._normalize_query(query)

        words = self._tokenize(normalized)

        word_count = len(words)

        query_lower = normalized.lower()

        # --------------------------------------------------------------
        # Empty query
        # --------------------------------------------------------------

        if not normalized:
            return QueryAnalysis(
                query="",
                intent=QueryIntent.FACTUAL,
                complexity=QueryComplexity.LOW,
                requires_retrieval=False,
                requires_multi_hop=False,
                requires_reranking=False,
                requires_multiple_queries=False,
                keywords=[],
                confidence=1.0,
            )

        # --------------------------------------------------------------
        # Intent
        # --------------------------------------------------------------

        intent = self._detect_intent(
            query_lower=query_lower,
            word_count=word_count,
        )

        # --------------------------------------------------------------
        # Complexity
        # --------------------------------------------------------------

        complexity = self._detect_complexity(
            word_count=word_count,
        )

        # --------------------------------------------------------------
        # Multi-hop requirement
        # --------------------------------------------------------------

        requires_multi_hop = self._requires_multi_hop(
            query_lower=query_lower,
            word_count=word_count,
        )

        # --------------------------------------------------------------
        # Multiple-query requirement
        # --------------------------------------------------------------

        requires_multiple_queries = (
            intent
            in {
                QueryIntent.COMPARATIVE,
                QueryIntent.EXPLORATORY,
            }
            or requires_multi_hop
        )

        # --------------------------------------------------------------
        # Reranking requirement
        # --------------------------------------------------------------

        requires_reranking = (
            complexity
            in {
                QueryComplexity.MEDIUM,
                QueryComplexity.HIGH,
            }
            or intent
            in {
                QueryIntent.COMPARATIVE,
                QueryIntent.ANALYTICAL,
            }
        )

        # --------------------------------------------------------------
        # Keywords
        # --------------------------------------------------------------

        keywords = self._extract_keywords(words)

        # --------------------------------------------------------------
        # Confidence
        # --------------------------------------------------------------

        confidence = self._calculate_confidence(
            query_lower=query_lower,
            word_count=word_count,
            intent=intent,
        )

        return QueryAnalysis(
            query=normalized,
            intent=intent,
            complexity=complexity,
            requires_retrieval=True,
            requires_multi_hop=requires_multi_hop,
            requires_reranking=requires_reranking,
            requires_multiple_queries=requires_multiple_queries,
            keywords=keywords,
            confidence=confidence,
        )

    # ==================================================================

    def create_plan(
        self,
        analysis: QueryAnalysis,
    ) -> RetrievalPlan:
        """
        Generate a retrieval plan from query analysis.

        Args:
            analysis:
                Previously generated QueryAnalysis.

        Returns:
            RetrievalPlan.

        Raises:
            TypeError:
                If analysis is not a QueryAnalysis instance.
        """

        if not isinstance(
            analysis,
            QueryAnalysis,
        ):
            raise TypeError(
                "analysis must be a QueryAnalysis instance"
            )

        # --------------------------------------------------------------
        # No retrieval required
        # --------------------------------------------------------------

        if not analysis.requires_retrieval:
            return RetrievalPlan(
                strategy=RetrievalStrategy.DIRECT,
                top_k=1,
                similarity_threshold=self._similarity_threshold(),
                max_queries=1,
                rerank=False,
                expand_query=False,
                multi_hop=False,
                fallback_strategies=[],
                reasoning=(
                    "Query does not require external retrieval."
                ),
            )

        # --------------------------------------------------------------
        # Select primary strategy
        # --------------------------------------------------------------

        strategy = self._select_strategy(
            analysis
        )

        # --------------------------------------------------------------
        # Select top-k
        # --------------------------------------------------------------

        top_k = self._select_top_k(
            analysis
        )

        # --------------------------------------------------------------
        # Reranking
        # --------------------------------------------------------------

        rerank = (
            analysis.requires_reranking
            and bool(
                getattr(
                    self.config,
                    "enable_reranking",
                    False,
                )
            )
        )

        # --------------------------------------------------------------
        # Query expansion
        # --------------------------------------------------------------

        enable_query_expansion = bool(
            getattr(
                self.config,
                "enable_query_expansion",
                False,
            )
        )

        expand_query = (
            analysis.requires_multiple_queries
            and enable_query_expansion
        )

        # --------------------------------------------------------------
        # Multi-hop
        # --------------------------------------------------------------

        enable_multi_hop = bool(
            getattr(
                self.config,
                "enable_multi_hop",
                False,
            )
        )

        multi_hop = (
            analysis.requires_multi_hop
            and enable_multi_hop
        )

        # --------------------------------------------------------------
        # Number of queries
        # --------------------------------------------------------------

        max_queries = self._select_max_queries(
            analysis=analysis,
            expand_query=expand_query,
        )

        # --------------------------------------------------------------
        # Fallback strategies
        # --------------------------------------------------------------

        fallback_strategies = (
            self._fallback_strategies(
                strategy
            )
        )

        # --------------------------------------------------------------
        # Similarity threshold
        # --------------------------------------------------------------

        similarity_threshold = (
            self._similarity_threshold()
        )

        # --------------------------------------------------------------
        # Reasoning
        # --------------------------------------------------------------

        reasoning = self._build_reasoning(
            analysis=analysis,
            strategy=strategy,
            top_k=top_k,
            rerank=rerank,
            expand_query=expand_query,
            multi_hop=multi_hop,
            max_queries=max_queries,
        )

        return RetrievalPlan(
            strategy=strategy,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            max_queries=max_queries,
            rerank=rerank,
            expand_query=expand_query,
            multi_hop=multi_hop,
            fallback_strategies=fallback_strategies,
            reasoning=reasoning,
        )

    # ==================================================================

    def plan(
        self,
        query: str,
    ) -> tuple[QueryAnalysis, RetrievalPlan]:
        """
        Analyze a query and generate its retrieval plan.

        This is the primary convenience API.

        Args:
            query:
                User query.

        Returns:
            Tuple of:

                (
                    QueryAnalysis,
                    RetrievalPlan,
                )
        """

        analysis = self.analyze_query(
            query
        )

        plan = self.create_plan(
            analysis
        )

        return analysis, plan

    # ==================================================================
    # INTENT DETECTION
    # ==================================================================

    def _detect_intent(
        self,
        query_lower: str,
        word_count: int,
    ) -> QueryIntent:
        """
        Determine the primary query intent.
        """

        if self._contains_any_term(
            query_lower,
            self.COMPARISON_TERMS,
        ):
            return QueryIntent.COMPARATIVE

        if self._contains_any_phrase(
            query_lower,
            self.SUMMARY_TERMS,
        ):
            return QueryIntent.SUMMARIZATION

        if self._contains_any_term(
            query_lower,
            self.ANALYTICAL_TERMS,
        ):
            return QueryIntent.ANALYTICAL

        if word_count <= 8:
            return QueryIntent.FACTUAL

        return QueryIntent.EXPLORATORY

    # ==================================================================

    @staticmethod
    def _detect_complexity(
        word_count: int,
    ) -> QueryComplexity:
        """
        Determine query complexity from query length.
        """

        if word_count <= 8:
            return QueryComplexity.LOW

        if word_count <= 20:
            return QueryComplexity.MEDIUM

        return QueryComplexity.HIGH

    # ==================================================================

    def _requires_multi_hop(
        self,
        query_lower: str,
        word_count: int,
    ) -> bool:
        """
        Determine whether the query likely requires multiple
        retrieval steps.
        """

        if word_count > 30:
            return True

        return self._contains_any_phrase(
            query_lower,
            self.MULTI_HOP_TERMS,
        )

    # ==================================================================
    # STRATEGY SELECTION
    # ==================================================================

    def _select_strategy(
        self,
        analysis: QueryAnalysis,
    ) -> RetrievalStrategy:
        """
        Select the primary retrieval strategy.

        Priority:

        1. Multi-hop
        2. Comparative
        3. Analytical
        4. Exploratory
        5. Summarization
        6. Configured default
        """

        if analysis.requires_multi_hop:
            return RetrievalStrategy.MULTI_QUERY

        if analysis.intent == QueryIntent.COMPARATIVE:
            return RetrievalStrategy.HYBRID

        if analysis.intent == QueryIntent.ANALYTICAL:
            return RetrievalStrategy.HYBRID

        if analysis.intent == QueryIntent.EXPLORATORY:
            return RetrievalStrategy.BROAD

        if analysis.intent == QueryIntent.SUMMARIZATION:
            return RetrievalStrategy.HYBRID

        default_strategy = getattr(
            self.config,
            "default_strategy",
            RetrievalStrategy.VECTOR,
        )

        return default_strategy

    # ==================================================================
    # TOP-K
    # ==================================================================

    def _select_top_k(
        self,
        analysis: QueryAnalysis,
    ) -> int:
        """
        Determine the number of retrieval candidates.

        Low complexity:
            <= 5

        Medium complexity:
            configured default

        High complexity:
            <= 20
        """

        max_context_chunks = self._positive_int(
            getattr(
                self.config,
                "max_context_chunks",
                20,
            ),
            default=20,
        )

        default_top_k = self._positive_int(
            getattr(
                self.config,
                "default_top_k",
                10,
            ),
            default=10,
        )

        if analysis.complexity == QueryComplexity.LOW:
            requested = 5

        elif analysis.complexity == QueryComplexity.HIGH:
            requested = 20

        else:
            requested = default_top_k

        return max(
            1,
            min(
                requested,
                max_context_chunks,
            ),
        )

    # ==================================================================
    # MAX QUERIES
    # ==================================================================

    def _select_max_queries(
        self,
        analysis: QueryAnalysis,
        expand_query: bool,
    ) -> int:
        """
        Determine the maximum number of generated/retrieved queries.
        """

        enable_multi_query = bool(
            getattr(
                self.config,
                "enable_multi_query",
                False,
            )
        )

        configured_max_queries = self._positive_int(
            getattr(
                self.config,
                "max_queries",
                3,
            ),
            default=3,
        )

        # If expansion or multi-query retrieval is disabled,
        # always execute the original query only.
        if not expand_query:
            return 1

        if not enable_multi_query:
            return 1

        if not analysis.requires_multiple_queries:
            return 1

        return max(
            1,
            min(
                configured_max_queries,
                5,
            ),
        )

    # ==================================================================
    # FALLBACK STRATEGIES
    # ==================================================================

    @staticmethod
    def _fallback_strategies(
        strategy: RetrievalStrategy,
    ) -> list[RetrievalStrategy]:
        """
        Return fallback retrieval strategies.

        The primary strategy is never included in the fallback list.
        """

        fallback_map: dict[
            RetrievalStrategy,
            list[RetrievalStrategy],
        ] = {
            RetrievalStrategy.VECTOR: [
                RetrievalStrategy.HYBRID,
                RetrievalStrategy.KEYWORD,
            ],
            RetrievalStrategy.KEYWORD: [
                RetrievalStrategy.HYBRID,
                RetrievalStrategy.VECTOR,
            ],
            RetrievalStrategy.HYBRID: [
                RetrievalStrategy.VECTOR,
                RetrievalStrategy.KEYWORD,
            ],
            RetrievalStrategy.MULTI_QUERY: [
                RetrievalStrategy.HYBRID,
                RetrievalStrategy.VECTOR,
            ],
            RetrievalStrategy.BROAD: [
                RetrievalStrategy.HYBRID,
                RetrievalStrategy.VECTOR,
            ],
            RetrievalStrategy.DIRECT: [],
        }

        return list(
            fallback_map.get(
                strategy,
                [
                    RetrievalStrategy.HYBRID,
                    RetrievalStrategy.VECTOR,
                ],
            )
        )

    # ==================================================================
    # KEYWORD EXTRACTION
    # ==================================================================

    @classmethod
    def _extract_keywords(
        cls,
        words: list[str],
    ) -> list[str]:
        """
        Extract useful keywords from tokenized query text.

        Preserves original order while removing duplicates.
        """

        keywords: list[str] = []

        seen: set[str] = set()

        for word in words:
            normalized = word.strip().lower()

            if not normalized:
                continue

            if normalized in cls.STOP_WORDS:
                continue

            if len(normalized) <= 2:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            keywords.append(normalized)

            if len(keywords) >= 15:
                break

        return keywords

    # ==================================================================
    # REASONING
    # ==================================================================

    @staticmethod
    def _build_reasoning(
        analysis: QueryAnalysis,
        strategy: RetrievalStrategy,
        top_k: int,
        rerank: bool,
        expand_query: bool,
        multi_hop: bool,
        max_queries: int,
    ) -> str:
        """
        Build human-readable reasoning for the generated plan.
        """

        parts = [
            (
                f"Query classified as "
                f"{analysis.intent.value} "
                f"with {analysis.complexity.value} complexity."
            ),
            (
                f"Selected {strategy.value} retrieval "
                f"with top_k={top_k}."
            ),
        ]

        if rerank:
            parts.append(
                "Reranking is enabled because the query "
                "requires higher retrieval precision."
            )

        if expand_query:
            parts.append(
                f"Query expansion is enabled with up to "
                f"{max_queries} queries."
            )

        if multi_hop:
            parts.append(
                "Multi-hop retrieval is enabled because "
                "the query likely requires multiple evidence steps."
            )

        return " ".join(parts)

    # ==================================================================
    # QUERY UTILITIES
    # ==================================================================

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:
        """
        Normalize user query whitespace safely.
        """

        if not isinstance(query, str):
            return ""

        return re.sub(
            r"\s+",
            " ",
            query.strip(),
        )

    # ==================================================================

    @staticmethod
    def _tokenize(
        query: str,
    ) -> list[str]:
        """
        Tokenize a normalized query.
        """

        if not query:
            return []

        return re.findall(
            r"\b[\w'-]+\b",
            query.lower(),
        )

    # ==================================================================

    @staticmethod
    def _contains_any_term(
        query: str,
        terms: frozenset[str],
    ) -> bool:
        """
        Check whether any complete word from terms occurs in query.
        """

        if not query:
            return False

        query_words = set(
            re.findall(
                r"\b[\w'-]+\b",
                query.lower(),
            )
        )

        return bool(
            query_words.intersection(terms)
        )

    # ==================================================================

    @staticmethod
    def _contains_any_phrase(
        query: str,
        phrases: tuple[str, ...] | frozenset[str],
    ) -> bool:
        """
        Check whether any phrase occurs in the query.
        """

        if not query:
            return False

        return any(
            phrase.lower() in query
            for phrase in phrases
        )

    # ==================================================================
    # CONFIDENCE
    # ==================================================================

    @staticmethod
    def _calculate_confidence(
        query_lower: str,
        word_count: int,
        intent: QueryIntent,
    ) -> float:
        """
        Calculate a deterministic confidence score.

        This is not model probability. It is simply a planner
        confidence indicator.

        Strong explicit intent signals receive higher confidence.
        """

        if not query_lower:
            return 1.0

        explicit_signals = (
            "compare",
            "comparison",
            "summarize",
            "summary",
            "analyze",
            "analysis",
            "explain",
            "evaluate",
        )

        has_explicit_signal = any(
            signal in query_lower
            for signal in explicit_signals
        )

        if has_explicit_signal:
            return 0.9

        if intent in {
            QueryIntent.FACTUAL,
            QueryIntent.EXPLORATORY,
        }:
            if word_count <= 3:
                return 0.8

            if word_count <= 15:
                return 0.75

            return 0.7

        return 0.7

    # ==================================================================
    # CONFIG UTILITIES
    # ==================================================================

    @staticmethod
    def _positive_int(
        value: object,
        default: int,
    ) -> int:
        """
        Safely convert a configuration value to a positive integer.
        """

        try:
            converted = int(value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return default

        if converted <= 0:
            return default

        return converted

    # ==================================================================

    def _similarity_threshold(self) -> float:
        """
        Safely obtain the configured similarity threshold.

        Keeps the value inside the valid [0, 1] range.
        """

        raw_value = getattr(
            self.config,
            "default_similarity_threshold",
            0.0,
        )

        try:
            value = float(raw_value)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

        if value != value:  # NaN
            return 0.0

        if value < 0.0:
            return 0.0

        if value > 1.0:
            return 1.0

        return value


__all__ = [
    "AdaptiveRAGPlanner",
]