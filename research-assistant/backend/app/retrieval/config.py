"""
Configuration for retrieval, reranking, and context compression.

These settings control the behavior of the post-retrieval pipeline.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalConfig:
    """Configuration for the retrieval pipeline."""

    # -------------------------
    # Retrieval
    # -------------------------
    INITIAL_TOP_K: int = 50
    FINAL_TOP_K: int = 10

    # -------------------------
    # Cross Encoder
    # -------------------------
    CROSS_ENCODER_MODEL: str = "BAAI/bge-reranker-base"

    # Batch size during inference
    RERANK_BATCH_SIZE: int = 16

    # -------------------------
    # Duplicate Removal
    # -------------------------
    REMOVE_EXACT_DUPLICATES: bool = True

    # Cosine similarity threshold
    SEMANTIC_DUPLICATE_THRESHOLD: float = 0.95

    # -------------------------
    # Context Compression
    # -------------------------
    ENABLE_COMPRESSION: bool = True

    # Maximum sentences to keep from each chunk
    MAX_SENTENCES_PER_CHUNK: int = 5

    # Minimum sentence length
    MIN_SENTENCE_LENGTH: int = 20

    # -------------------------
    # Token Budget
    # -------------------------
    MAX_CONTEXT_TOKENS: int = 6000

    RESERVED_SYSTEM_TOKENS: int = 1000
    RESERVED_RESPONSE_TOKENS: int = 1000

    # -------------------------
    # Context Ordering
    # -------------------------
    ORDER_BY_RELEVANCE: bool = True

    # -------------------------
    # Misc
    # -------------------------
    RANDOM_SEED: int = 42


# Global configuration instance
retrieval_config = RetrievalConfig()