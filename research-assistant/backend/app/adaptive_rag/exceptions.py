"""
Adaptive RAG exceptions.

All exceptions specific to the Adaptive RAG subsystem live here.
"""


class AdaptiveRAGError(Exception):
    """
    Base exception for all Adaptive RAG errors.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "ADAPTIVE_RAG_ERROR",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return self.message


class AdaptiveRAGConfigurationError(AdaptiveRAGError):
    """
    Raised when Adaptive RAG configuration is invalid.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="CONFIGURATION_ERROR",
        )


class AdaptiveRAGPlanningError(AdaptiveRAGError):
    """
    Raised when query planning fails.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="PLANNING_ERROR",
        )


class AdaptiveRAGRoutingError(AdaptiveRAGError):
    """
    Raised when routing fails.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="ROUTING_ERROR",
        )


class AdaptiveRAGRetrievalError(AdaptiveRAGError):
    """
    Raised when retrieval fails.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="RETRIEVAL_ERROR",
        )


class AdaptiveRAGEvaluationError(AdaptiveRAGError):
    """
    Raised when retrieval/context evaluation fails.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="EVALUATION_ERROR",
        )


class AdaptiveRAGGenerationError(AdaptiveRAGError):
    """
    Raised when answer generation fails.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="GENERATION_ERROR",
        )


class AdaptiveRAGMaxRetriesExceeded(AdaptiveRAGError):
    """
    Raised when Adaptive RAG cannot improve retrieval
    after the configured number of retries.
    """

    def __init__(self, message: str = "Maximum Adaptive RAG retries exceeded.") -> None:
        super().__init__(
            message,
            code="MAX_RETRIES_EXCEEDED",
        )


class AdaptiveRAGStateError(AdaptiveRAGError):
    """
    Raised when the Adaptive RAG state is invalid.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="STATE_ERROR",
        )