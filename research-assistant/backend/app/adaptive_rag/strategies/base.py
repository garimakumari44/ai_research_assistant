"""
Base interfaces for Adaptive RAG strategies.

Strategies define HOW retrieval should be performed.
The adaptive controller decides WHEN and WHICH strategy to use.

Responsibilities
----------------
- Define the common strategy interface.
- Provide a consistent strategy result.
- Keep concrete retrieval strategies decoupled from the controller.
- Support both generic retrievers and the application's
  retrieval-service naming convention.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(slots=True)
class StrategyResult:
    """
    Standard result returned by every RAG strategy.
    """

    answer: str | None = None

    documents: list[Any] = field(default_factory=list)

    confidence: float = 0.0

    strategy: str = ""

    iterations: int = 1

    queries: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    success: bool = True

    error: str | None = None

    @property
    def has_documents(self) -> bool:
        """
        Return True when the strategy retrieved at least one document.
        """
        return bool(self.documents)


class BaseRAGStrategy(ABC):
    """
    Abstract base class for all Adaptive RAG strategies.

    Concrete implementations should only focus on their
    retrieval/reasoning behavior. Strategy selection belongs
    to the router/controller.

    Dependency compatibility
    ------------------------
    The strategy accepts both:

        retriever=...

    and:

        retrieval_service=...

    The application currently uses ``retrieval_service`` in the
    AdaptiveRAGController, while the generic strategy interface
    uses ``retriever`` internally.

    Both are normalized to ``self.retriever``.
    """

    name: str = "base"

    def __init__(
        self,
        retriever: Any = None,
        generator: Any = None,
        evaluator: Any = None,
        retrieval_service: Any = None,
        **_: Any,
    ) -> None:
        """
        Initialize the strategy.

        Parameters
        ----------
        retriever:
            Generic retrieval dependency.

        generator:
            RAG answer generator.

        evaluator:
            Strategy-level evaluator.

        retrieval_service:
            Application-level retrieval service.

            This is supported as an alias for ``retriever`` because
            the controller currently passes the dependency using this
            name.
        """

        # Prefer the explicitly supplied generic retriever.
        #
        # If it is not provided, fall back to the application's
        # retrieval_service dependency.
        self.retriever = (
            retriever
            if retriever is not None
            else retrieval_service
        )

        self.generator = generator
        self.evaluator = evaluator

    # ==================================================================
    # EXECUTION
    # ==================================================================

    @abstractmethod
    async def execute(
        self,
        query: str,
        *,
        context: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> StrategyResult:
        """
        Execute the strategy.

        Parameters
        ----------
        query:
            User query.

        context:
            Optional execution context shared by the
            adaptive controller.

        Returns
        -------
        StrategyResult
        """
        raise NotImplementedError

    # ==================================================================
    # RETRIEVAL
    # ==================================================================

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        **kwargs: Any,
    ) -> Sequence[Any]:
        """
        Generic retriever adapter.

        Supports retrievers exposing either:

            - async retrieve()
            - async search()
            - synchronous retrieve()
            - synchronous search()

        The method deliberately keeps the strategy independent from
        the concrete retrieval implementation.
        """

        if self.retriever is None:
            return []

        if hasattr(
            self.retriever,
            "retrieve",
        ):
            result = self.retriever.retrieve(
                query,
                top_k=top_k,
                **kwargs,
            )

        elif hasattr(
            self.retriever,
            "search",
        ):
            result = self.retriever.search(
                query,
                top_k=top_k,
                **kwargs,
            )

        else:
            raise AttributeError(
                "Retriever must expose 'retrieve' or 'search'."
            )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        return result or []

    # ==================================================================
    # GENERATION
    # ==================================================================

    async def generate(
        self,
        query: str,
        documents: Sequence[Any],
        **kwargs: Any,
    ) -> str:
        """
        Generic generator adapter.

        Supports generators exposing either:

            - generate()
            - answer()
        """

        if self.generator is None:
            return ""

        if hasattr(
            self.generator,
            "generate",
        ):
            result = self.generator.generate(
                query=query,
                documents=documents,
                **kwargs,
            )

        elif hasattr(
            self.generator,
            "answer",
        ):
            result = self.generator.answer(
                query=query,
                documents=documents,
                **kwargs,
            )

        else:
            raise AttributeError(
                "Generator must expose 'generate' or 'answer'."
            )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        return str(result or "")

    # ==================================================================
    # EVALUATION
    # ==================================================================

    async def evaluate(
        self,
        query: str,
        answer: str,
        documents: Sequence[Any],
        **kwargs: Any,
    ) -> float:
        """
        Generic evaluator adapter.

        Returns a normalized confidence score in [0, 1].

        Supports evaluators exposing either:

            - evaluate()
            - score()
        """

        if self.evaluator is None:
            return 0.0

        if hasattr(
            self.evaluator,
            "evaluate",
        ):
            result = self.evaluator.evaluate(
                query=query,
                answer=answer,
                documents=documents,
                **kwargs,
            )

        elif hasattr(
            self.evaluator,
            "score",
        ):
            result = self.evaluator.score(
                query=query,
                answer=answer,
                documents=documents,
                **kwargs,
            )

        else:
            raise AttributeError(
                "Evaluator must expose 'evaluate' or 'score'."
            )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        try:
            return max(
                0.0,
                min(
                    1.0,
                    float(result),
                ),
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0

    # ==================================================================
    # RESULT
    # ==================================================================

    def build_result(
        self,
        *,
        answer: str | None = None,
        documents: Sequence[Any] | None = None,
        confidence: float = 0.0,
        iterations: int = 1,
        queries: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
        success: bool = True,
        error: str | None = None,
    ) -> StrategyResult:
        """
        Build a normalized StrategyResult.

        Confidence and iteration values are normalized here so every
        strategy returns a consistent representation.
        """

        return StrategyResult(
            answer=answer,
            documents=list(
                documents or []
            ),
            confidence=max(
                0.0,
                min(
                    1.0,
                    confidence,
                ),
            ),
            strategy=self.name,
            iterations=max(
                1,
                iterations,
            ),
            queries=list(
                queries or []
            ),
            metadata=dict(
                metadata or {}
            ),
            success=success,
            error=error,
        )


__all__ = [
    "StrategyResult",
    "BaseRAGStrategy",
]