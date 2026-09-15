"""
Graph-augmented RAG strategy.

Combines:

    Query
      ↓
    Vector retrieval
      +
    Graph retrieval
      ↓
    Context fusion
      ↓
    Generation
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .base import BaseRAGStrategy, StrategyResult


class GraphAugmentedRAGStrategy(BaseRAGStrategy):
    """
    RAG strategy that augments vector retrieval with
    knowledge-graph context.
    """

    name = "graph_augmented"

    def __init__(
        self,
        retriever: Any = None,
        generator: Any = None,
        evaluator: Any = None,
        graph_store: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            retriever=retriever,
            generator=generator,
            evaluator=evaluator,
            **kwargs,
        )

        self.graph_store = graph_store

    async def graph_search(
        self,
        query: str,
        **kwargs: Any,
    ) -> Sequence[Any]:
        """
        Retrieve graph-derived context.

        Supports common graph interfaces:
            - search()
            - query()
            - retrieve()
        """

        if self.graph_store is None:
            return []

        if hasattr(self.graph_store, "search"):
            result = self.graph_store.search(
                query,
                **kwargs,
            )

        elif hasattr(self.graph_store, "query"):
            result = self.graph_store.query(
                query,
                **kwargs,
            )

        elif hasattr(self.graph_store, "retrieve"):
            result = self.graph_store.retrieve(
                query,
                **kwargs,
            )

        else:
            raise AttributeError(
                "Graph store must expose search, query, or retrieve."
            )

        if hasattr(result, "__await__"):
            result = await result

        return result or []

    @staticmethod
    def merge_context(
        vector_documents: Sequence[Any],
        graph_documents: Sequence[Any],
    ) -> list[Any]:
        """
        Merge vector and graph evidence while preserving order.
        """

        merged: list[Any] = []
        seen: set[Any] = set()

        for document in [
            *vector_documents,
            *graph_documents,
        ]:

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
            merged.append(document)

        return merged

    async def execute(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
        top_k: int = 5,
        **kwargs: Any,
    ) -> StrategyResult:

        try:
            vector_documents = list(
                await self.retrieve(
                    query,
                    top_k=top_k,
                    **kwargs,
                )
            )

            graph_documents = list(
                await self.graph_search(
                    query,
                    **kwargs,
                )
            )

            documents = self.merge_context(
                vector_documents,
                graph_documents,
            )

            if not documents:
                return self.build_result(
                    documents=[],
                    queries=[query],
                    success=False,
                    error="No vector or graph evidence was found.",
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
                iterations=1,
                queries=[query],
                metadata={
                    "vector_documents": len(vector_documents),
                    "graph_documents": len(graph_documents),
                    "merged_documents": len(documents),
                    "graph_enabled": self.graph_store is not None,
                },
            )

        except Exception as exc:
            return self.build_result(
                queries=[query],
                success=False,
                error=str(exc),
            )