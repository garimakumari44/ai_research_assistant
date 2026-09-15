"""
Direct RAG strategy.

Pipeline:
    query
      ↓
    retrieve
      ↓
    generate
      ↓
    evaluate
      ↓
    result
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import BaseRAGStrategy, StrategyResult


class DirectRAGStrategy(BaseRAGStrategy):
    """
    Single-pass retrieval augmented generation.
    """

    name = "direct"

    async def execute(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
        top_k: int = 5,
        evaluate: bool = True,
        **kwargs: Any,
    ) -> StrategyResult:

        try:
            documents = await self.retrieve(
                query,
                top_k=top_k,
                **kwargs,
            )

            if not documents:
                return self.build_result(
                    answer=None,
                    documents=[],
                    confidence=0.0,
                    queries=[query],
                    success=False,
                    error="No relevant documents were retrieved.",
                )

            answer = await self.generate(
                query,
                documents,
                context=context,
                **kwargs,
            )

            confidence = 0.0

            if evaluate and answer:
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
                iterations=1,
                queries=[query],
                metadata={
                    "retrieval_count": len(documents),
                    "evaluation_enabled": evaluate,
                },
            )

        except Exception as exc:
            return self.build_result(
                queries=[query],
                success=False,
                error=str(exc),
            )