"""
Assistant domain models.

Canonical request, response, conversation, context, source, citation,
LLM, execution, error, and status schemas for the assistant layer.

Architecture:

    AssistantRequest
          |
          v
    Assistant
          |
          v
    AssistantOrchestrator
          |
          +----> ConversationContext
          |
          +----> Retrieval
          |
          +----> Research
          |
          +----> Adaptive RAG
          |
          +----> LLM
          |
          v
    AssistantResponse

This module contains DATA CONTRACTS ONLY.

Business logic belongs in:
    - assistant.py
    - context.py
    - orchestrator.py
    - response.py
    - prompts.py
    - retrieval/
    - research/
    - adaptive_rag/
    - llm/
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# HELPERS
# ============================================================================


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# ============================================================================
# ENUMS
# ============================================================================


class AssistantMode(str, Enum):
    """High-level assistant execution mode."""

    AUTO = "auto"
    CHAT = "chat"
    RAG = "rag"
    RETRIEVAL = "retrieval"
    RESEARCH = "research"
    ANALYSIS = "analysis"


class ResponseFormat(str, Enum):
    """Requested response format."""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"


class CitationStyle(str, Enum):
    """Citation rendering preference."""

    NONE = "none"
    INLINE = "inline"
    FOOTNOTE = "footnote"


class MessageRole(str, Enum):
    """Standard conversational roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ============================================================================
# CONVERSATION MODELS
# ============================================================================


class ChatMessage(BaseModel):
    """Canonical conversational message."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    role: str = Field(
        ...,
        min_length=1,
    )

    content: str = ""

    name: Optional[str] = None

    tool_call_id: Optional[str] = None

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


# Backward-compatible name used by older assistant modules.
AssistantMessage = ChatMessage


# ============================================================================
# SOURCE / EVIDENCE
# ============================================================================


class SourceReference(BaseModel):
    """
    Canonical source reference.

    Supports documents, chunks, web sources, papers, repositories,
    research results, and provider-specific sources.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    id: Optional[str] = None

    title: Optional[str] = None

    source: Optional[str] = None

    source_type: str = "other"

    url: Optional[str] = None

    document_id: Optional[str] = None

    chunk_id: Optional[str] = None

    collection_id: Optional[str] = None

    content: Optional[str] = None

    authors: List[str] = Field(
        default_factory=list,
    )

    score: Optional[float] = None

    relevance_score: Optional[float] = None

    similarity_score: Optional[float] = None

    rank: Optional[int] = None

    page: Optional[int] = None

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


AssistantSource = SourceReference


# ============================================================================
# CITATIONS
# ============================================================================


class Citation(BaseModel):
    """Citation attached to an assistant answer."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    id: Optional[str] = None

    source_id: Optional[str] = None

    document_id: Optional[str] = None

    chunk_id: Optional[str] = None

    title: Optional[str] = None

    url: Optional[str] = None

    text: Optional[str] = None

    quote: Optional[str] = None

    page: Optional[int] = None

    position: Optional[int] = None

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


AssistantCitation = Citation


# ============================================================================
# LLM RESPONSE
# ============================================================================


class LLMResponse(BaseModel):
    """
    Canonical normalized response from an LLM provider.

    The orchestrator converts provider-specific responses into this model
    before passing them to the response layer.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
    )

    content: str = ""

    model: Optional[str] = None

    provider: Optional[str] = None

    usage: Dict[str, Any] = Field(
        default_factory=dict,
    )

    finish_reason: Optional[str] = None

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )




# ============================================================================
# EXECUTION
# ============================================================================


class AssistantExecution(BaseModel):
    """Metadata describing one assistant execution."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    execution_id: str = Field(
        ...,
        min_length=1,
    )

    mode: str = "chat"

    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
    )

    llm_used: bool = False

    retrieval_used: bool = False

    research_used: bool = False

    source_count: int = Field(
        default=0,
        ge=0,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )


# ============================================================================
# REQUEST
# ============================================================================


class AssistantRequest(BaseModel):
    """
    Main request contract for the assistant.

    Supports:

        - normal chat
        - RAG
        - retrieval
        - research
        - analysis
        - Adaptive RAG
        - conversation history
        - provider/model selection
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    # ------------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------------

    query: str = Field(
        ...,
        min_length=1,
        description="User question or instruction.",
    )

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    request_id: Optional[str] = None

    session_id: Optional[str] = None

    conversation_id: Optional[str] = None

    user_id: Optional[str] = None

    # ------------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------------

    mode: AssistantMode = AssistantMode.AUTO

    # ------------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------------

    messages: List[ChatMessage] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------------

    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    retrieval_enabled: bool = True

    use_retrieval: Optional[bool] = None

    # ------------------------------------------------------------------------
    # Research
    # ------------------------------------------------------------------------

    research: bool = False

    research_enabled: Optional[bool] = None

    use_research: Optional[bool] = None

    # ------------------------------------------------------------------------
    # Adaptive RAG
    # ------------------------------------------------------------------------

    use_adaptive_rag: bool = True

    adaptive_rag_enabled: Optional[bool] = None

    # ------------------------------------------------------------------------
    # Knowledge scope
    # ------------------------------------------------------------------------

    document_ids: List[str] = Field(
        default_factory=list,
    )

    collection_ids: List[str] = Field(
        default_factory=list,
    )

    knowledge_base_id: Optional[str] = None

    # ------------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------------

    model: Optional[str] = None

    provider: Optional[str] = None

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
    )

    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
    )

    # ------------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------------

    response_format: ResponseFormat = ResponseFormat.MARKDOWN

    citation_style: CitationStyle = CitationStyle.INLINE

    include_citations: bool = True

    include_sources: bool = True

    # ------------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------------

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    context: Dict[str, Any] = Field(
        default_factory=dict,
    )

    # ========================================================================
    # COMPATIBILITY PROPERTIES
    # ========================================================================

    @property
    def message(self) -> str:
        """
        Backward-compatible singular message accessor.

        Older assistant modules use request.message while the canonical
        contract uses request.query.
        """
        return self.query

    @property
    def history(self) -> List[ChatMessage]:
        """
        Backward-compatible conversation history accessor.
        """
        return self.messages

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    def is_research_request(self) -> bool:
        """Return whether this request should use research."""

        return (
            self.mode == AssistantMode.RESEARCH
            or self.research
            or self.research_enabled is True
            or self.use_research is True
        )

    def is_retrieval_request(self) -> bool:
        """Return whether retrieval should be used."""

        if self.use_retrieval is not None:
            return self.use_retrieval

        if self.mode in {
            AssistantMode.RAG,
            AssistantMode.RETRIEVAL,
        }:
            return True

        return self.retrieval_enabled

    def is_adaptive_rag_enabled(self) -> bool:
        """Return whether Adaptive RAG is enabled."""

        if self.adaptive_rag_enabled is not None:
            return self.adaptive_rag_enabled

        return self.use_adaptive_rag

    def build_context(self) -> "AssistantContext":
        """Build the initial execution context."""

        return AssistantContext(
            request=self,
            request_id=self.request_id,
            session_id=self.session_id,
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            query=self.query,
            mode=self.mode,
            messages=list(self.messages),
            document_ids=list(self.document_ids),
            collection_ids=list(self.collection_ids),
            knowledge_base_id=self.knowledge_base_id,
            retrieval_enabled=self.is_retrieval_request(),
            research_enabled=self.is_research_request(),
            adaptive_rag_enabled=self.is_adaptive_rag_enabled(),
            provider=self.provider,
            model=self.model,
            metadata=dict(self.metadata),
            state=dict(self.context),
        )


# ============================================================================
# ASSISTANT CONTEXT
# ============================================================================


class AssistantContext(BaseModel):
    """
    Mutable runtime state shared throughout assistant execution.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    # ------------------------------------------------------------------------
    # Original request
    # ------------------------------------------------------------------------

    request: Optional[AssistantRequest] = None

    # ------------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------------

    request_id: Optional[str] = None

    session_id: Optional[str] = None

    conversation_id: Optional[str] = None

    user_id: Optional[str] = None

    # ------------------------------------------------------------------------
    # Query / mode
    # ------------------------------------------------------------------------

    query: str = ""

    mode: AssistantMode = AssistantMode.CHAT

    # ------------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------------

    messages: List[ChatMessage] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------------

    sources: List[SourceReference] = Field(
        default_factory=list,
    )

    citations: List[Citation] = Field(
        default_factory=list,
    )

    retrieved_documents: List[Dict[str, Any]] = Field(
        default_factory=list,
    )

    retrieved_context: List[Any] = Field(
        default_factory=list,
    )

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
    )

    retrieval_state: Dict[str, Any] = Field(
        default_factory=dict,
    )

    evidence_state: Dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # Research
    # ------------------------------------------------------------------------

    research_result: Any = None

    research_state: Dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # Knowledge scope
    # ------------------------------------------------------------------------

    document_ids: List[str] = Field(
        default_factory=list,
    )

    collection_ids: List[str] = Field(
        default_factory=list,
    )

    knowledge_base_id: Optional[str] = None

    # ------------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------------

    retrieval_enabled: bool = True

    research_enabled: bool = False

    adaptive_rag_enabled: bool = True

    # ------------------------------------------------------------------------
    # Adaptive RAG
    # ------------------------------------------------------------------------

    adaptive_rag_state: Dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------------

    provider: Optional[str] = None

    model: Optional[str] = None

    routing_decision: Dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # Prompt / answer
    # ------------------------------------------------------------------------

    system_prompt: Optional[str] = None

    assembled_context: Optional[str] = None

    draft_answer: Optional[str] = None

    final_answer: Optional[str] = None

    # ------------------------------------------------------------------------
    # Generic state
    # ------------------------------------------------------------------------

    state: Dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    # ------------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------------

    errors: List[str] = Field(
        default_factory=list,
    )

    warnings: List[str] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------------

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
    )

    # ========================================================================
    # COMPATIBILITY
    # ========================================================================

    @property
    def conversation(self) -> List[ChatMessage]:
        """
        Backward-compatible alias for messages.
        """
        return self.messages

    @conversation.setter
    def conversation(
        self,
        value: Sequence[ChatMessage],
    ) -> None:
        self.messages = list(value)

    # ========================================================================
    # MESSAGE HELPERS
    # ========================================================================

    def add_message(
        self,
        role: str,
        content: str,
        *,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """Add a message."""

        message = ChatMessage(
            role=role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            metadata=metadata or {},
        )

        self.messages.append(message)
        self.touch()

        return message

    def add_user_message(
        self,
        content: str,
    ) -> ChatMessage:
        """Add a user message."""

        return self.add_message(
            MessageRole.USER.value,
            content,
        )

    def add_assistant_message(
        self,
        content: str,
    ) -> ChatMessage:
        """Add an assistant message."""

        return self.add_message(
            MessageRole.ASSISTANT.value,
            content,
        )

    def add_system_message(
        self,
        content: str,
    ) -> ChatMessage:
        """Add a system message."""

        return self.add_message(
            MessageRole.SYSTEM.value,
            content,
        )

    # ========================================================================
    # SOURCE HELPERS
    # ========================================================================

    def add_source(
        self,
        source: SourceReference,
    ) -> None:
        """Add a source."""

        self.sources.append(source)
        self.touch()

    def add_sources(
        self,
        sources: Sequence[SourceReference],
    ) -> None:
        """Add multiple sources."""

        self.sources.extend(sources)
        self.touch()

    # ========================================================================
    # CITATION HELPERS
    # ========================================================================

    def add_citation(
        self,
        citation: Citation,
    ) -> None:
        """Add a citation."""

        self.citations.append(citation)
        self.touch()

    def add_citations(
        self,
        citations: Sequence[Citation],
    ) -> None:
        """Add multiple citations."""

        self.citations.extend(citations)
        self.touch()

    # ========================================================================
    # STATE
    # ========================================================================

    def set_state(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.state[key] = value
        self.touch()

    def get_state(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.state.get(
            key,
            default,
        )

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.metadata[key] = value
        self.touch()

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.metadata.get(
            key,
            default,
        )

    # ========================================================================
    # ERRORS
    # ========================================================================

    def add_error(
        self,
        message: str,
    ) -> None:
        if message:
            self.errors.append(str(message))

        self.touch()

    def add_warning(
        self,
        message: str,
    ) -> None:
        if message:
            self.warnings.append(str(message))

        self.touch()

    def has_errors(self) -> bool:
        return bool(self.errors)

    def has_warnings(self) -> bool:
        return bool(self.warnings)

    # ========================================================================
    # RETRIEVAL
    # ========================================================================

    def has_sources(self) -> bool:
        return bool(
            self.sources
            or self.retrieved_documents
            or self.retrieved_context
            or self.evidence
        )

    def clear_retrieval(self) -> None:
        self.sources.clear()
        self.citations.clear()
        self.retrieved_documents.clear()
        self.retrieved_context.clear()
        self.evidence.clear()

        self.retrieval_state.clear()
        self.evidence_state.clear()

        self.touch()

    # ========================================================================
    # TIMESTAMP
    # ========================================================================

    def touch(self) -> None:
        self.updated_at = utc_now()


# ============================================================================
# RESPONSE
# ============================================================================


class AssistantResponse(BaseModel):
    """Canonical assistant response."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )

    # Stable response-builder contract
    id: Optional[str] = None

    message: str = ""

    status: str = "completed"

    execution: Optional[AssistantExecution] = None

    # Backward-compatible answer/response fields
    answer: str = ""

    response: Optional[str] = None

    request_id: Optional[str] = None

    session_id: Optional[str] = None

    conversation_id: Optional[str] = None

    mode: AssistantMode = AssistantMode.CHAT

    citations: List[Citation] = Field(
        default_factory=list,
    )

    sources: List[SourceReference] = Field(
        default_factory=list,
    )

    retrieved_documents: int = 0

    evidence_count: int = 0

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    model: Optional[str] = None

    provider: Optional[str] = None

    latency_ms: Optional[float] = None

    usage: Dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )


AssistantResult = AssistantResponse


# ============================================================================
# STREAMING
# ============================================================================


class AssistantChunk(BaseModel):
    """Streaming assistant response chunk."""

    model_config = ConfigDict(
        extra="allow",
    )

    content: str = ""

    done: bool = False

    request_id: Optional[str] = None

    session_id: Optional[str] = None

    conversation_id: Optional[str] = None

    citations: List[Citation] = Field(
        default_factory=list,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


AssistantChunkResponse = AssistantChunk


# ============================================================================
# ERROR
# ============================================================================


class AssistantError(BaseModel):
    """Structured assistant error."""

    model_config = ConfigDict(
        extra="allow",
    )

    code: str = Field(
        ...,
        min_length=1,
    )

    message: str = Field(
        ...,
        min_length=1,
    )

    retryable: bool = False

    details: Dict[str, Any] = Field(
        default_factory=dict,
    )

    timestamp: datetime = Field(
        default_factory=utc_now,
    )


# ============================================================================
# STATUS
# ============================================================================


class AssistantStatus(BaseModel):
    """Runtime assistant subsystem status."""

    model_config = ConfigDict(
        extra="allow",
    )

    available: bool = True

    llm_available: bool = False

    retrieval_available: bool = False

    research_available: bool = False

    adaptive_rag_available: bool = False

    provider: Optional[str] = None

    model: Optional[str] = None

    details: Dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# PUBLIC API
# ============================================================================


__all__ = [
    "utc_now",

    # Enums
    "AssistantMode",
    "ResponseFormat",
    "CitationStyle",
    "MessageRole",

    # Conversation
    "ChatMessage",
    "AssistantMessage",

    # Sources
    "SourceReference",
    "AssistantSource",

    # Citations
    "Citation",
    "AssistantCitation",

    # LLM
    "LLMResponse",

    # Execution
    "AssistantExecution",

    # Context
    "AssistantContext",

    # Request
    "AssistantRequest",

    # Response
    "AssistantResponse",
    "AssistantResult",

    # Streaming
    "AssistantChunk",
    "AssistantChunkResponse",

    # Errors/status
    "AssistantError",
    "AssistantStatus",
]