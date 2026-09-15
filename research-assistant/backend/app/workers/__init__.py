"""
Celery worker task package.

This package contains asynchronous/background tasks for:

- document ingestion
- chunk embedding generation
- vector/knowledge indexing
- RAG evaluation
- cleanup and maintenance

Tasks should remain orchestration-focused. Business logic belongs in
the corresponding application/domain services.
"""

from __future__ import annotations

__all__ = [
    "cleanup",
    "embeddings",
    "evaluation",
    "indexing",
    "ingestion",
]