"""
Generation layer.

Responsible for transforming selected evidence into a grounded
natural-language answer and verifying the result.
"""

from .citation import (
    Citation,
    CitationManager,
    CitationValidation,
    extract_citations,
    validate_citations,
)

from .llm import (
    BaseLLM,
    LLMConfig,
    LLMError,
    OllamaLLM,
    OpenAICompatibleLLM,
    create_llm,
)

from .synthesizer import (
    AnswerSynthesizer,
    EvidenceFormatter,
    EvidenceItem,
    GeneratedAnswer,
)

from .verifier import (
    AnswerVerifier,
    VerificationError,
    VerificationResult,
    VerificationThresholds,
    verify_citation_integrity,
)

__all__ = [
    "AnswerSynthesizer",
    "AnswerVerifier",
    "BaseLLM",
    "Citation",
    "CitationManager",
    "CitationValidation",
    "EvidenceFormatter",
    "EvidenceItem",
    "GeneratedAnswer",
    "LLMConfig",
    "LLMError",
    "OllamaLLM",
    "OpenAICompatibleLLM",
    "VerificationError",
    "VerificationResult",
    "VerificationThresholds",
    "create_llm",
    "extract_citations",
    "validate_citations",
    "verify_citation_integrity",
]