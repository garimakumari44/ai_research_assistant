"""
Chunking package for the Adaptive Research RAG system.

This package provides multiple document chunking strategies:

- BaseChunker: common chunker interface
- SemanticChunker: sentence/meaning-aware chunking
- StructuralChunker: section/paragraph-aware chunking
- ChunkingStrategy: strategy selector/orchestrator
"""

from app.knowledge.chunking.base import (
    BaseChunker,
    Chunk,
    ChunkingConfig,
    ChunkingResult,
)
from app.knowledge.chunking.semantic import SemanticChunker
from app.knowledge.chunking.structural import StructuralChunker
from app.knowledge.chunking.strategy import ChunkingStrategy

__all__ = [
    "BaseChunker",
    "Chunk",
    "ChunkingConfig",
    "ChunkingResult",
    "SemanticChunker",
    "StructuralChunker",
    "ChunkingStrategy",
]