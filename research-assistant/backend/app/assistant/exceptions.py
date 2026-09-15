from __future__ import annotations


class AssistantError(Exception):
    """Base exception for assistant-layer failures."""

    default_message = "Assistant operation failed."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str = "assistant_error",
    ) -> None:
        self.code = code
        self.message = message or self.default_message
        super().__init__(self.message)


class AssistantValidationError(AssistantError):
    """Raised when assistant input is invalid."""

    default_message = "Invalid assistant request."

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="validation_error",
        )


class AssistantConfigurationError(AssistantError):
    """Raised when assistant dependencies are incorrectly configured."""

    default_message = "Assistant configuration is invalid."

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="configuration_error",
        )


class AssistantLLMError(AssistantError):
    """Raised when the LLM layer fails."""

    default_message = "The language model failed to generate a response."

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="llm_error",
        )


class AssistantResearchError(AssistantError):
    """Raised when research execution fails."""

    default_message = "Research execution failed."

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="research_error",
        )


class AssistantRetrievalError(AssistantError):
    """Raised when retrieval execution fails."""

    default_message = "Retrieval execution failed."

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="retrieval_error",
        )


class AssistantResponseError(AssistantError):
    """Raised when an LLM/service response cannot be normalized."""

    default_message = "Assistant response could not be normalized."

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="response_error",
        )