"""
Cache key generation utilities.

Provides a centralized way to generate Redis cache keys.
"""

from __future__ import annotations

import hashlib


class CacheKeys:
    """
    Helper methods for generating cache keys.
    """

    # ==========================================================
    # Users
    # ==========================================================

    @staticmethod
    def user(user_id: int | str) -> str:
        return f"user:{user_id}"

    @staticmethod
    def user_profile(user_id: int | str) -> str:
        return f"user:{user_id}:profile"

    @staticmethod
    def user_permissions(user_id: int | str) -> str:
        return f"user:{user_id}:permissions"

    # ==========================================================
    # Authentication
    # ==========================================================

    @staticmethod
    def access_token(token_id: str) -> str:
        return f"auth:access:{token_id}"

    @staticmethod
    def refresh_token(token_id: str) -> str:
        return f"auth:refresh:{token_id}"

    @staticmethod
    def login_attempt(email: str) -> str:
        return f"auth:login:{email.lower()}"

    # ==========================================================
    # Documents
    # ==========================================================

    @staticmethod
    def document(document_id: int | str) -> str:
        return f"document:{document_id}"

    @staticmethod
    def document_chunks(document_id: int | str) -> str:
        return f"document:{document_id}:chunks"

    @staticmethod
    def document_metadata(document_id: int | str) -> str:
        return f"document:{document_id}:metadata"

    # ==========================================================
    # Embeddings
    # ==========================================================

    @staticmethod
    def embedding(text: str) -> str:
        digest = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

        return f"embedding:{digest}"

    # ==========================================================
    # Retrieval
    # ==========================================================

    @staticmethod
    def retrieval(query: str) -> str:
        digest = hashlib.sha256(
            query.encode("utf-8")
        ).hexdigest()

        return f"retrieval:{digest}"

    @staticmethod
    def rerank(query: str) -> str:
        digest = hashlib.sha256(
            query.encode("utf-8")
        ).hexdigest()

        return f"rerank:{digest}"

    # ==========================================================
    # Research
    # ==========================================================

    @staticmethod
    def research(job_id: str) -> str:
        return f"research:{job_id}"

    @staticmethod
    def report(report_id: str) -> str:
        return f"report:{report_id}"

    # ==========================================================
    # Evaluation
    # ==========================================================

    @staticmethod
    def evaluation(run_id: str) -> str:
        return f"evaluation:{run_id}"

    # ==========================================================
    # Rate Limiting
    # ==========================================================

    @staticmethod
    def rate_limit(identifier: str) -> str:
        return f"rate_limit:{identifier}"

    # ==========================================================
    # Generic
    # ==========================================================

    @staticmethod
    def namespace(
        namespace: str,
        key: str,
    ) -> str:
        return f"{namespace}:{key}"