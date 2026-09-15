"""
Stopping policy for Adaptive RAG.

Determines whether the retrieval/generation loop should continue.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StoppingDecision:
    should_stop: bool
    reason: str
    confidence: float


class StoppingPolicy:
    """
    Controls when Adaptive RAG should stop retrieving.

    The policy prevents:
    - unnecessary retrieval iterations
    - infinite loops
    - repeated low-value searches
    """

    def __init__(
        self,
        *,
        confidence_threshold: float = 0.80,
        minimum_confidence_threshold: float = 0.45,
        max_iterations: int = 4,
        min_information_gain: float = 0.05,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.minimum_confidence_threshold = minimum_confidence_threshold
        self.max_iterations = max_iterations
        self.min_information_gain = min_information_gain

    def should_stop(
        self,
        *,
        iteration: int,
        confidence: float,
        information_gain: float = 1.0,
        has_sufficient_context: bool = False,
        answerable: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> StoppingDecision:
        """
        Determine whether Adaptive RAG should stop.

        Parameters
        ----------
        iteration:
            Current retrieval iteration.

        confidence:
            Current answer/retrieval confidence in [0, 1].

        information_gain:
            Estimated information gained during the latest iteration.

        has_sufficient_context:
            Whether the current context is sufficient.

        answerable:
            Whether the system believes the question is answerable.
        """

        confidence = self._clamp(confidence)
        information_gain = self._clamp(information_gain)

        if iteration >= self.max_iterations:
            return StoppingDecision(
                should_stop=True,
                reason="Maximum retrieval iterations reached.",
                confidence=confidence,
            )

        if not answerable:
            return StoppingDecision(
                should_stop=True,
                reason="The query cannot currently be answered reliably.",
                confidence=confidence,
            )

        if (
            confidence >= self.confidence_threshold
            and has_sufficient_context
        ):
            return StoppingDecision(
                should_stop=True,
                reason=(
                    "Confidence is above the stopping threshold and "
                    "sufficient context is available."
                ),
                confidence=confidence,
            )

        if information_gain < self.min_information_gain:
            if confidence >= self.minimum_confidence_threshold:
                return StoppingDecision(
                    should_stop=True,
                    reason=(
                        "Additional retrieval is producing insufficient "
                        "information gain."
                    ),
                    confidence=confidence,
                )

        return StoppingDecision(
            should_stop=False,
            reason="Additional retrieval may improve the answer.",
            confidence=confidence,
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))