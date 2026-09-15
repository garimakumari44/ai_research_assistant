from __future__ import annotations

import re
from typing import List

from app.retrieval.models import (
    QueryAnalysis,
    QueryType,
    RetrievalDecision,
    RetrievalQuery,
)


# ============================================================================
# QUERY PROCESSOR
# ============================================================================


class QueryProcessor:
    """
    Handles safe preprocessing of research queries.

    Important:
        We do NOT aggressively remove punctuation.

    Research queries often contain meaningful expressions such as:

        BERT-base-uncased
        GPT-4o
        RAG@5
        Recall@10
        LoRA/QLoRA
        arXiv:2401.12345
    """

    def normalize(
        self,
        query: str,
    ) -> str:
        """
        Normalize whitespace and casing.
        """

        if not query:
            return ""

        query = query.strip()

        query = re.sub(
            r"\s+",
            " ",
            query,
        )

        return query.lower()

    def remove_special_characters(
        self,
        query: str,
    ) -> str:
        """
        Preserve meaningful research punctuation.

        Only removes control characters.
        """

        if not query:
            return ""

        return "".join(
            char
            for char in query
            if char.isprintable()
        )

    def tokenize(
        self,
        query: str,
    ) -> List[str]:
        """
        Lightweight tokenization.

        This intentionally preserves tokens such as:
            gpt-4o
            bert-base
            rag@10
        """

        if not query:
            return []

        return re.findall(
            r"[A-Za-z0-9_@./:+#-]+",
            query,
        )

    def extract_keywords(
        self,
        query: str,
    ) -> List[str]:
        """
        Extract useful lexical terms.
        """

        tokens = self.tokenize(query)

        stop_words = {
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
            "this",
            "to",
            "what",
            "when",
            "where",
            "which",
            "who",
            "why",
            "with",
        }

        return [
            token
            for token in tokens
            if token not in stop_words
        ]

    def expand_query(
        self,
        query: str,
    ) -> List[str]:
        """
        Query expansion hook.

        Adaptive RAG can later plug in:
            - LLM rewriting
            - synonyms
            - HyDE
            - domain terminology expansion
            - multi-query generation
        """

        if not query:
            return []

        return [query]

    def process(
        self,
        query: RetrievalQuery,
    ) -> RetrievalQuery:
        """
        Complete preprocessing pipeline.
        """

        cleaned = self.normalize(
            query.query
        )

        cleaned = self.remove_special_characters(
            cleaned
        )

        return query.model_copy(
            update={
                "query": cleaned,
            }
        )

    def analyze(
        self,
        query: str,
    ) -> QueryAnalysis:
        """
        Produce a lightweight query analysis object.
        """

        normalized = self.normalize(
            query
        )

        normalized = self.remove_special_characters(
            normalized
        )

        keywords = self.extract_keywords(
            normalized
        )

        query_type = QueryRouter().detect_type(
            normalized
        )

        return QueryAnalysis(
            original_query=query,
            normalized_query=normalized,
            keywords=keywords,
            query_type=query_type,
            confidence=0.8,
        )


# ============================================================================
# QUERY ROUTER
# ============================================================================


class QueryRouter:
    """
    Determines the retrieval mechanism.

    This router only chooses the retrieval MODE.

    It does NOT choose Adaptive RAG strategies.

    Example:

        keyword-heavy query
            -> BM25

        conceptual query
            -> dense

        mixed research query
            -> hybrid
    """

    SEMANTIC_KEYWORDS = {
        "explain",
        "why",
        "how",
        "difference",
        "compare",
        "relationship",
        "impact",
        "effect",
        "architecture",
        "approach",
        "method",
        "limitations",
        "advantages",
        "disadvantages",
    }

    KEYWORD_PATTERNS = (
        r"\bexactly\b",
        r"\btitle\b",
        r"\bauthor\b",
        r"\bpaper\b",
        r"\bdoi\b",
        r"\barxiv\b",
        r"\byear\b",
    )

    def detect_type(
        self,
        query: str,
    ) -> QueryType:
        """
        Classify query into keyword, semantic, or hybrid.
        """

        lower = query.lower()

        tokens = set(
            QueryProcessor().tokenize(
                lower
            )
        )

        semantic_hits = len(
            tokens.intersection(
                self.SEMANTIC_KEYWORDS
            )
        )

        keyword_hits = sum(
            1
            for pattern in self.KEYWORD_PATTERNS
            if re.search(
                pattern,
                lower,
            )
        )

        if semantic_hits > 0 and keyword_hits > 0:
            return "hybrid"

        if semantic_hits > 0:
            return "semantic"

        if keyword_hits > 0:
            return "keyword"

        # Research questions generally benefit from both.
        return "hybrid"

    def route(
        self,
        query: str,
    ) -> str:
        """
        Return the concrete retrieval mode.
        """

        query_type = self.detect_type(
            query
        )

        if query_type == "semantic":
            return "dense"

        if query_type == "keyword":
            return "bm25"

        return "hybrid"

    def decide(
        self,
        query: str,
    ) -> RetrievalDecision:
        """
        Return a structured routing decision.
        """

        query_type = self.detect_type(
            query
        )

        mode = self.route(
            query
        )

        return RetrievalDecision(
            mode=mode,
            query_type=query_type,
            confidence=0.8,
            reason=(
                f"Query classified as "
                f"{query_type}; selected {mode} retrieval."
            ),
        )


__all__ = [
    "QueryProcessor",
    "QueryRouter",
]