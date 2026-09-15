"""
Corrective RAG strategy.

Pipeline:

    query
      ↓
    retrieve
      ↓
    evaluate retrieval
      ↓
   good? ───── yes ──→ generate
    │
    no
    ↓
  reformulate
    ↓
  retrieve again
    ↓
  generate
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import BaseRAGStrategy, StrategyResult


class CorrectiveRAGStrategy(BaseRAGStrategy):
    """
    Retrieval-quality-aware RAG strategy.
    """

    name = "corrective"

    def __init__(
        self,
        retriever: Any = None,
        generator: Any = None,
        evaluator: Any = None,
        retrieval_threshold: float = 0.60,
        max_corrections: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            retriever=retriever,
            generator=generator,
            evaluator=evaluator,
            **kwargs,
        )

        self.retrieval_threshold = max(
            0.0,
            min(1.0, retrieval_threshold),
        )

        self.max_corrections = max(0, max_corrections)

    async def evaluate_retrieval(
        self,
        query: str,
        documents: list[Any],
        **_: Any,
    ) -> float:
        """
        Estimate retrieval quality.

        If a dedicated retrieval evaluator exists, use it.
        Otherwise use a conservative document-presence signal.
        """

        if not documents:
            return 0.0

        if self.evaluator is not None:

            if hasattr(self.evaluator, "evaluate_retrieval"):
                result = self.evaluator.evaluate_retrieval(
                    query=query,
                    documents=documents,
                )

                if hasattr(result, "__await__"):
                    result = await result

                try:
                    return max(0.0, min(1.0, float(result)))
                except (TypeError, ValueError):
                    pass

        return 1.0 if documents else 0.0

    async def correct_query(
        self,
        query: str,
        documents: list[Any],
        correction_index: int,
        **_: Any,
    ) -> str:
        """
        Reformulate a weak query.

        Replace with an LLM-based corrective query generator
        in a production implementation.
        """

        return f"{query} specific evidence details"

    async def execute(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
        top_k: int = 5,
        **kwargs: Any,
    ) -> StrategyResult:

        current_query = query
        queries = [query]

        corrections = 0
        documents: list[Any] = []

        try:
            while corrections <= self.max_corrections:

                documents = list(
                    await self.retrieve(
                        current_query,
                        top_k=top_k,
                        **kwargs,
                    )
                )

                retrieval_score = await self.evaluate_retrieval(
                    current_query,
                    documents,
                    **kwargs,
                )

                if retrieval_score >= self.retrieval_threshold:
                    break

                if corrections >= self.max_corrections:
                    break

                corrections += 1

                current_query = await self.correct_query(
                    current_query,
                    documents,
                    corrections,
                    **kwargs,
                )

                queries.append(current_query)

            if not documents:
                return self.build_result(
                    queries=queries,
                    iterations=corrections + 1,
                    success=False,
                    error="Corrective retrieval produced no documents.",
                )

            answer = await self.generate(
                query,
                documents,
                context=context,
                **kwargs,
            )

            confidence = await self.evaluate(
                query,
                answer,
                documents,
                context=context,
                **kwargs,
            )

            return self.build_result(
                answer=answer,
                documents=documents,
                confidence=confidence,
                iterations=corrections + 1,
                queries=queries,
                metadata={
                    "corrections": corrections,
                    "retrieval_threshold": self.retrieval_threshold,
                },
            )

        except Exception as exc:
            return self.build_result(
                documents=documents,
                queries=queries,
                iterations=corrections + 1,
                success=False,
                error=str(exc),
            )