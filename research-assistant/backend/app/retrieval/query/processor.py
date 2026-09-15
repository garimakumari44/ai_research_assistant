from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.retrieval.models import RetrievalQuery

from app.retrieval.query.analyzer import QueryAnalyzer
from app.retrieval.query.classifier import QueryClassifier
from app.retrieval.query.rewriter import QueryRewriter


class QueryProcessor:
    """
    Coordinates query understanding before retrieval.

    Responsibilities
    ----------------
    QueryProcessor is the canonical query-understanding boundary.

    Pipeline:

        RetrievalQuery
             ↓
        QueryProcessor
             ├── QueryAnalyzer
             ├── QueryClassifier
             └── QueryRewriter
             ↓
        RetrievalQuery

    Important contract
    ------------------
    process() accepts and returns RetrievalQuery.

    The processor must never silently convert a RetrievalQuery into a
    plain string because downstream retrieval needs access to the
    complete request configuration.
    """

    def __init__(
        self,
        *,
        analyzer: QueryAnalyzer | None = None,
        classifier: QueryClassifier | None = None,
        rewriter: QueryRewriter | None = None,
    ) -> None:
        self.analyzer = analyzer or QueryAnalyzer()
        self.classifier = classifier or QueryClassifier()
        self.rewriter = rewriter or QueryRewriter()

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def process(
        self,
        request: RetrievalQuery,
    ) -> RetrievalQuery:
        """
        Process a canonical RetrievalQuery.

        The returned object remains a RetrievalQuery so the retrieval
        pipeline has one stable request contract.
        """

        if not isinstance(request, RetrievalQuery):
            raise TypeError(
                "request must be a RetrievalQuery instance"
            )

        original_query = self._normalize_query(
            request.query
        )

        if not original_query:
            return self._copy_query(
                request,
                query="",
            )

        # --------------------------------------------------------------
        # 1. Analyze
        # --------------------------------------------------------------

        analysis = self._analyze(
            original_query
        )

        # --------------------------------------------------------------
        # 2. Classify
        # --------------------------------------------------------------

        classification = self._classify(
            original_query,
            analysis,
        )

        # --------------------------------------------------------------
        # 3. Rewrite
        # --------------------------------------------------------------

        rewritten_query = self._rewrite(
            original_query,
            analysis,
            classification,
        )

        if not rewritten_query:
            rewritten_query = original_query

        rewritten_query = self._normalize_query(
            rewritten_query
        )

        if not rewritten_query:
            rewritten_query = original_query

        # --------------------------------------------------------------
        # 4. Preserve request metadata
        # --------------------------------------------------------------

        metadata = dict(
            request.metadata or {}
        )

        metadata.update(
            {
                "query_analysis": self._safe_model_dump(
                    analysis
                ),
                "query_classification": self._safe_model_dump(
                    classification
                ),
                "original_query": original_query,
                "processed_query": rewritten_query,
            }
        )

        return self._copy_query(
            request,
            query=rewritten_query,
            metadata=metadata,
        )

    # ==================================================================
    # ANALYSIS
    # ==================================================================

    def _analyze(
        self,
        query: str,
    ) -> Any:
        """
        Run query analysis.

        Analyzer failure is intentionally non-fatal. Retrieval can
        continue using the normalized query.
        """

        try:
            return self.analyzer.analyze(
                query
            )
        except Exception:
            # Query understanding is an enhancement, not a reason to
            # completely disable retrieval.
            return None

    # ==================================================================
    # CLASSIFICATION
    # ==================================================================

    def _classify(
        self,
        query: str,
        analysis: Any,
    ) -> Any:
        """
        Classify the query.

        Prefer the richer classifier interface when available.
        """

        try:
            if analysis is not None:
                try:
                    return self.classifier.classify(
                        query,
                        analysis=analysis,
                    )
                except TypeError:
                    pass

            return self.classifier.classify(
                query
            )

        except Exception:
            return None

    # ==================================================================
    # REWRITING
    # ==================================================================

    def _rewrite(
        self,
        query: str,
        analysis: Any,
        classification: Any,
    ) -> str:
        """
        Rewrite the query for retrieval.

        The original normalized query is retained if rewriting fails.
        """

        try:
            result = None

            # ----------------------------------------------------------
            # Richest interface
            # ----------------------------------------------------------

            try:
                result = self.rewriter.rewrite(
                    query,
                    analysis=analysis,
                    classification=classification,
                )
            except TypeError:
                pass

            # ----------------------------------------------------------
            # Analysis-only interface
            # ----------------------------------------------------------

            if result is None:
                try:
                    result = self.rewriter.rewrite(
                        query,
                        analysis=analysis,
                    )
                except TypeError:
                    pass

            # ----------------------------------------------------------
            # Basic interface
            # ----------------------------------------------------------

            if result is None:
                result = self.rewriter.rewrite(
                    query
                )

            rewritten = self._extract_rewritten_query(
                result
            )

            return rewritten or query

        except Exception:
            return query

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_query(
        query: Any,
    ) -> str:
        """
        Normalize whitespace without changing semantic meaning.
        """

        if query is None:
            return ""

        if not isinstance(query, str):
            query = str(query)

        return " ".join(
            query.strip().split()
        )

    # ==================================================================
    # QUERY COPYING
    # ==================================================================

    @staticmethod
    def _copy_query(
        request: RetrievalQuery,
        **updates: Any,
    ) -> RetrievalQuery:
        """
        Create a modified RetrievalQuery while preserving all existing
        fields.
        """

        if hasattr(
            request,
            "model_copy",
        ):
            return request.model_copy(
                update=updates
            )

        try:
            return replace(
                request,
                **updates,
            )
        except TypeError:
            # Explicit fallback for older/dataclass-style models.
            data = {}

            for field_name in (
                "query",
                "top_k",
                "filters",
                "mode",
                "vector_weight",
                "keyword_weight",
                "metadata",
                "enable_reranking",
            ):
                if hasattr(
                    request,
                    field_name,
                ):
                    data[field_name] = getattr(
                        request,
                        field_name,
                    )

            data.update(
                updates
            )

            return RetrievalQuery(
                **data
            )

    # ==================================================================
    # RESULT EXTRACTION
    # ==================================================================

    @staticmethod
    def _extract_rewritten_query(
        result: Any,
    ) -> str | None:
        """
        Extract the rewritten query from supported return types.
        """

        if result is None:
            return None

        if isinstance(
            result,
            str,
        ):
            value = result.strip()
            return value or None

        if isinstance(
            result,
            dict,
        ):
            for key in (
                "query",
                "rewritten_query",
                "text",
            ):
                value = result.get(
                    key
                )

                if isinstance(
                    value,
                    str,
                ):
                    value = value.strip()

                    if value:
                        return value

            return None

        for attribute in (
            "query",
            "rewritten_query",
            "text",
        ):
            value = getattr(
                result,
                attribute,
                None,
            )

            if isinstance(
                value,
                str,
            ):
                value = value.strip()

                if value:
                    return value

        return None

    # ==================================================================
    # MODEL SERIALIZATION
    # ==================================================================

    @staticmethod
    def _safe_model_dump(
        value: Any,
    ) -> Any:
        """
        Safely serialize query-understanding results for metadata.
        """

        if value is None:
            return None

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                return value.model_dump(
                    mode="json"
                )
            except Exception:
                pass

        if hasattr(
            value,
            "dict",
        ):
            try:
                return value.dict()
            except Exception:
                pass

        if isinstance(
            value,
            dict,
        ):
            return dict(
                value
            )

        return str(value)


__all__ = [
    "QueryProcessor",
]