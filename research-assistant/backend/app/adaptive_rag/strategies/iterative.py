"""
Iterative Adaptive RAG strategy.

Pipeline:

    query
      ↓
    retrieve
      ↓
    generate
      ↓
    evaluate
      ↓
    confident? ── yes → finish
       │
       no
       ↓
    refine query
       ↓
    retrieve again

The strategy maintains a deduplicated evidence collection across
iterations. Repeated retrieval of the same chunk must not produce
duplicate sources in the final result.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import BaseRAGStrategy, StrategyResult


class IterativeRAGStrategy(BaseRAGStrategy):
    """
    Repeated retrieval and generation strategy.

    Retrieval results from multiple iterations are merged by stable
    chunk/document identity so that the final evidence collection does
    not contain duplicate chunks.
    """

    name = "iterative"

    def __init__(
        self,
        retriever: Any = None,
        generator: Any = None,
        evaluator: Any = None,
        max_iterations: int = 3,
        confidence_threshold: float = 0.80,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            retriever=retriever,
            generator=generator,
            evaluator=evaluator,
            **kwargs,
        )

        self.max_iterations = max(
            1,
            int(max_iterations),
        )

        self.confidence_threshold = max(
            0.0,
            min(
                1.0,
                float(confidence_threshold),
            ),
        )

    # ==================================================================
    # Query refinement
    # ==================================================================

    async def refine_query(
        self,
        query: str,
        answer: str | None,
        documents: list[Any],
        iteration: int,
        **_: Any,
    ) -> str:
        """
        Produce the next retrieval query.

        A production implementation can replace this with an
        LLM-based query reformulator.
        """

        if not answer:
            return query

        return f"{query} additional evidence"

    # ==================================================================
    # Document identity
    # ==================================================================

    @staticmethod
    def _document_identity(
        document: Any,
    ) -> str:
        """
        Return a stable identity for a retrieved document/chunk.

        RetrievalResult normally has:

            document.id

        but this method also supports dictionaries and generic objects
        so the strategy remains compatible with the broader Adaptive
        RAG runtime.
        """

        # --------------------------------------------------------------
        # RetrievalResult-like object
        # --------------------------------------------------------------

        nested_document = getattr(
            document,
            "document",
            None,
        )

        if nested_document is not None:
            nested_id = getattr(
                nested_document,
                "id",
                None,
            )

            if nested_id is not None:
                return str(
                    nested_id
                )

        # --------------------------------------------------------------
        # Direct object
        # --------------------------------------------------------------

        direct_id = getattr(
            document,
            "id",
            None,
        )

        if direct_id is not None:
            return str(
                direct_id
            )

        # --------------------------------------------------------------
        # Dictionary
        # --------------------------------------------------------------

        if isinstance(
            document,
            Mapping,
        ):
            nested = document.get(
                "document"
            )

            if isinstance(
                nested,
                Mapping,
            ):
                nested_id = nested.get(
                    "id"
                )

                if nested_id is not None:
                    return str(
                        nested_id
                    )

            direct_id = document.get(
                "id"
            )

            if direct_id is not None:
                return str(
                    direct_id
                )

            document_id = document.get(
                "document_id"
            )

            chunk_id = document.get(
                "chunk_id"
            )

            if chunk_id is not None:
                return (
                    f"chunk:{chunk_id}"
                )

            if document_id is not None:
                return (
                    f"document:{document_id}"
                )

        # --------------------------------------------------------------
        # Last-resort identity
        # --------------------------------------------------------------

        return f"object:{id(document)}"

    # ==================================================================
    # Deduplication
    # ==================================================================

    @classmethod
    def _merge_documents(
        cls,
        existing: list[Any],
        new_documents: list[Any],
    ) -> list[Any]:
        """
        Merge retrieval results while preserving first-seen order.

        If a chunk is retrieved in multiple iterations, only the first
        occurrence is retained.

        This deliberately preserves the original retrieval result
        object rather than converting it into another model.
        """

        merged = list(
            existing
        )

        seen: set[str] = set()

        for document in merged:
            seen.add(
                cls._document_identity(
                    document
                )
            )

        for document in new_documents:
            identity = cls._document_identity(
                document
            )

            if identity in seen:
                continue

            seen.add(
                identity
            )

            merged.append(
                document
            )

        return merged

    # ==================================================================
    # Runtime configuration
    # ==================================================================

    def _runtime_max_iterations(
        self,
        context: Mapping[str, Any] | None,
    ) -> int:
        """
        Resolve max_iterations from runtime context when provided.

        The controller owns request-level execution configuration.
        """

        if context is None:
            return self.max_iterations

        value = context.get(
            "max_iterations"
        )

        if value is None:
            return self.max_iterations

        try:
            normalized = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return self.max_iterations

        return max(
            1,
            normalized,
        )

    def _runtime_confidence_threshold(
        self,
        context: Mapping[str, Any] | None,
    ) -> float:
        """
        Resolve confidence threshold from runtime context when provided.
        """

        if context is None:
            return self.confidence_threshold

        value = context.get(
            "confidence_threshold"
        )

        if value is None:
            return self.confidence_threshold

        try:
            normalized = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return self.confidence_threshold

        return max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )

    # ==================================================================
    # Execution
    # ==================================================================

    async def execute(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
        top_k: int = 5,
        **kwargs: Any,
    ) -> StrategyResult:
        """
        Execute iterative retrieval and generation.

        Important:

        `kwargs` passed here must contain only actual retrieval
        parameters. Controller-level execution controls such as
        max_iterations and confidence_threshold are read from context
        instead.
        """

        current_query = query

        all_documents: list[Any] = []
        queries: list[str] = []

        best_answer: str | None = None
        best_confidence = 0.0

        max_iterations = (
            self._runtime_max_iterations(
                context
            )
        )

        confidence_threshold = (
            self._runtime_confidence_threshold(
                context
            )
        )

        try:
            for iteration in range(
                1,
                max_iterations + 1,
            ):

                queries.append(
                    current_query
                )

                # ------------------------------------------------------
                # Retrieve
                # ------------------------------------------------------

                documents = list(
                    await self.retrieve(
                        current_query,
                        top_k=top_k,
                        **kwargs,
                    )
                )

                # ------------------------------------------------------
                # Merge WITHOUT duplicates
                # ------------------------------------------------------

                all_documents = (
                    self._merge_documents(
                        all_documents,
                        documents,
                    )
                )

                if not documents:
                    continue

                # ------------------------------------------------------
                # Generate
                # ------------------------------------------------------

                answer = await self.generate(
                    current_query,
                    documents,
                    context=context,
                    **kwargs,
                )

                # ------------------------------------------------------
                # Evaluate
                # ------------------------------------------------------

                confidence = await self.evaluate(
                    current_query,
                    answer,
                    documents,
                    context=context,
                    **kwargs,
                )

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_answer = answer

                # ------------------------------------------------------
                # Confidence-based early stopping
                # ------------------------------------------------------

                if confidence >= confidence_threshold:
                    return self.build_result(
                        answer=answer,
                        documents=all_documents,
                        confidence=confidence,
                        iterations=iteration,
                        queries=queries,
                        metadata={
                            "stopped_reason": (
                                "confidence_threshold"
                            ),
                            "threshold": (
                                confidence_threshold
                            ),
                            "unique_documents": (
                                len(all_documents)
                            ),
                            "last_iteration_documents": (
                                len(documents)
                            ),
                        },
                    )

                # ------------------------------------------------------
                # Refine query for next iteration
                # ------------------------------------------------------

                current_query = await self.refine_query(
                    current_query,
                    answer,
                    documents,
                    iteration,
                    **kwargs,
                )

            # ----------------------------------------------------------
            # Maximum iterations reached
            # ----------------------------------------------------------

            return self.build_result(
                answer=best_answer,
                documents=all_documents,
                confidence=best_confidence,
                iterations=max_iterations,
                queries=queries,
                metadata={
                    "stopped_reason": "max_iterations",
                    "max_iterations": max_iterations,
                    "unique_documents": len(
                        all_documents
                    ),
                },
            )

        except Exception as exc:
            return self.build_result(
                answer=best_answer,
                documents=all_documents,
                confidence=best_confidence,
                iterations=len(
                    queries
                ) or 1,
                queries=queries,
                success=False,
                error=str(exc),
                metadata={
                    "unique_documents": len(
                        all_documents
                    ),
                },
            )