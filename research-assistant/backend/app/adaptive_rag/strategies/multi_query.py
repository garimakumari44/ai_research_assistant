"""
Multi-query RAG strategy.

Pipeline:

    original query
          ↓
    query expansion
       ↙  ↓  ↘
     q1   q2   q3
      ↓   ↓    ↓
    retrieve for each
          ↓
       merge
          ↓
       generate
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .base import BaseRAGStrategy, StrategyResult


class MultiQueryRAGStrategy(BaseRAGStrategy):
    """
    Retrieve using multiple query formulations.
    """

    name = "multi_query"

    def __init__(
        self,
        retriever: Any = None,
        generator: Any = None,
        evaluator: Any = None,
        max_queries: int = 3,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            retriever=retriever,
            generator=generator,
            evaluator=evaluator,
            **kwargs,
        )

        self.max_queries = max(1, max_queries)

    async def expand_query(
        self,
        query: str,
        **_: Any,
    ) -> Sequence[str]:
        """
        Generate alternative query formulations.

        Replace this implementation with an LLM-based query
        expansion service when available.
        """

        return [
            query,
            f"{query} explanation",
            f"{query} evidence",
        ][: self.max_queries]

    @staticmethod
    def deduplicate_documents(
        documents: Sequence[Any],
    ) -> list[Any]:
        """
        Remove duplicate retrieved documents.

        Supports common document representations:
            - objects with id
            - objects with document_id
            - dictionaries
            - fallback object identity
        """

        unique: list[Any] = []
        seen: set[Any] = set()

        for document in documents:

            if isinstance(document, dict):
                key = (
                    document.get("id")
                    or document.get("document_id")
                    or document.get("chunk_id")
                )
            else:
                key = (
                    getattr(document, "id", None)
                    or getattr(document, "document_id", None)
                    or getattr(document, "chunk_id", None)
                )

            if key is None:
                key = id(document)

            if key in seen:
                continue

            seen.add(key)
            unique.append(document)

        return unique

    async def execute(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
        top_k: int = 5,
        **kwargs: Any,
    ) -> StrategyResult:

        try:
            queries = list(
                await self.expand_query(
                    query,
                    context=context,
                    **kwargs,
                )
            )

            queries = queries[: self.max_queries]

            all_documents: list[Any] = []

            for expanded_query in queries:
                documents = await self.retrieve(
                    expanded_query,
                    top_k=top_k,
                    **kwargs,
                )

                all_documents.extend(documents)

            unique_documents = self.deduplicate_documents(
                all_documents
            )

            if not unique_documents:
                return self.build_result(
                    documents=[],
                    queries=queries,
                    success=False,
                    error="No relevant documents found.",
                )

            answer = await self.generate(
                query,
                unique_documents,
                context=context,
                **kwargs,
            )

            confidence = await self.evaluate(
                query,
                answer,
                unique_documents,
                context=context,
                **kwargs,
            )

            return self.build_result(
                answer=answer,
                documents=unique_documents,
                confidence=confidence,
                iterations=1,
                queries=queries,
                metadata={
                    "generated_queries": len(queries),
                    "retrieved_documents": len(all_documents),
                    "unique_documents": len(unique_documents),
                },
            )

        except Exception as exc:
            return self.build_result(
                queries=[query],
                success=False,
                error=str(exc),
            )