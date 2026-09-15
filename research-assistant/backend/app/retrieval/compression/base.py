from __future__ import annotations

from abc import ABC, abstractmethod

from app.retrieval.compression.models import (
    CompressionRequest,
    CompressionResult,
)


class BaseCompressor(ABC):
    """
    Abstract base class for all context compression components.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable compressor name.
        """
        raise NotImplementedError

    @abstractmethod
    def compress(
        self,
        request: CompressionRequest,
    ) -> CompressionResult:
        """
        Compress the retrieved context.

        Args:
            request: Compression request.

        Returns:
            CompressionResult
        """
        raise NotImplementedError