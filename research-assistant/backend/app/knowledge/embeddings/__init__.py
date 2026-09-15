"""
Embedding subsystem for the Adaptive Research RAG platform.

This package provides:

- BaseEmbeddingProvider
- EmbeddingConfig
- EmbeddingResult
- EmbeddingProvider
- EmbeddingService
"""

from app.knowledge.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingResult,
)
from app.knowledge.embeddings.provider import (
    EmbeddingProvider,
)
from app.knowledge.embeddings.service import (
    EmbeddingService,
)

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingProvider",
    "EmbeddingService",
]