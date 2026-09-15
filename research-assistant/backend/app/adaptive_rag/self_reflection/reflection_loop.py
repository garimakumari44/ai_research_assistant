from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any, Callable, Mapping, Sequence

from .answer_checker import AnswerChecker
from .critic import Critic, CriticResult, CriticSeverity
from .gap_detector import GapDetector, GapDetectionResult
from .hallucination_detector import (
    HallucinationDetector,
    HallucinationResult,
)
from .retrieval_checker import (
    RetrievalChecker,
    RetrievalCheckResult,
)

logger = logging.getLogger(__name__)


class ReflectionStatus(str, Enum):
    ACCEPTED = "accepted"
    RETRIEVAL_REQUIRED = "retrieval_required"
    REGENERATION_REQUIRED = "regeneration_required"
    MAX_ITERATIONS = "max_iterations"
    FAILED = "failed"


class ReflectionDecision(str, Enum):
    ACCEPT = "accept"
    RETRIEVE = "retrieve"
    REGENERATE = "regenerate"
    STOP = "stop"


@dataclass(frozen=True)
class ReflectionConfig:
    """
    Runtime configuration for the reflection loop.
    """

    max_iterations: int = 3
    stop_on_critical: bool = True
    allow_regeneration: bool = True
    allow_additional_retrieval: bool = True

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")


@dataclass(frozen=True)
class ReflectionIteration:
    iteration: int
    decision: ReflectionDecision
    critic: CriticResult
    retrieval: RetrievalCheckResult
    gaps: GapDetectionResult
    answer: Any
    hallucination: HallucinationResult
    answer_check: Any


@dataclass(frozen=True)
class ReflectionResult:
    status: ReflectionStatus
    final_answer: Any
    iterations: tuple[ReflectionIteration, ...]
    final_critic: CriticResult | None
    total_iterations: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        return self.status == ReflectionStatus.ACCEPTED


RetrieveFn = Callable[
    [str, Sequence[Any], Sequence[str]],
    Sequence[Any],
]

GenerateFn = Callable[
    [str, Sequence[Any], Any, CriticResult],
    Any,
]


class ReflectionLoop:
    """
    Production-oriented self-reflection coordinator.

    Responsibilities
    ----------------
    1. Evaluate retrieved evidence.
    2. Evaluate the generated answer.
    3. Detect unsupported claims.
    4. Decide whether to accept, retrieve again, or regenerate.
    5. Prevent infinite reflection loops.
    6. Preserve iteration history for observability.

    The loop does NOT:
        - own a vector database
        - own an LLM client
        - perform network calls
        - mutate global application state

    Integration example
    -------------------
        result = loop.run(
            query=query,
            answer=answer,
            evidence=evidence,
            retrieve=retrieve_fn,
            generate=generate_fn,
        )
    """

    def __init__(
        self,
        *,
        config: ReflectionConfig | None = None,
        retrieval_checker: RetrievalChecker | None = None,
        gap_detector: GapDetector | None = None,
        answer_checker: AnswerChecker | None = None,
        hallucination_detector: HallucinationDetector | None = None,
        critic: Critic | None = None,
    ) -> None:
        self.config = config or ReflectionConfig()

        self.retrieval_checker = (
            retrieval_checker or RetrievalChecker()
        )

        self.gap_detector = (
            gap_detector or GapDetector()
        )

        self.answer_checker = (
            answer_checker or AnswerChecker()
        )

        self.hallucination_detector = (
            hallucination_detector
            or HallucinationDetector()
        )

        self.critic = critic or Critic()

    def run(
        self,
        *,
        query: str,
        answer: Any,
        evidence: Sequence[Any] | None,
        retrieve: RetrieveFn | None = None,
        generate: GenerateFn | None = None,
    ) -> ReflectionResult:
        """
        Execute the reflection loop.

        Parameters
        ----------
        query:
            Original user query.

        answer:
            Initial generated answer.

        evidence:
            Initial retrieved evidence.

        retrieve:
            Optional retrieval callback.

        generate:
            Optional answer-generation callback.

        Returns
        -------
        ReflectionResult
        """

        if not query or not query.strip():
            raise ValueError("query must not be empty")

        current_answer = answer
        current_evidence = list(evidence or [])

        history: list[ReflectionIteration] = []

        for iteration in range(1, self.config.max_iterations + 1):
            try:
                retrieval_result = self.retrieval_checker.check(
                    query,
                    current_evidence,
                )

                gap_result = self.gap_detector.detect(
                    query,
                    current_evidence,
                )

                answer_result = self.answer_checker.check(
                    query,
                    self._answer_text(current_answer),
                    current_evidence,
                )

                hallucination_result = (
                    self.hallucination_detector.detect(
                        self._answer_text(current_answer),
                        current_evidence,
                    )
                )

                critic_result = self.critic.evaluate(
                    retrieval=retrieval_result,
                    gaps=gap_result,
                    answer=answer_result,
                    hallucination=hallucination_result,
                )

                decision = self._decide(
                    critic_result,
                    iteration,
                )

                iteration_record = ReflectionIteration(
                    iteration=iteration,
                    decision=decision,
                    critic=critic_result,
                    retrieval=retrieval_result,
                    gaps=gap_result,
                    answer=current_answer,
                    hallucination=hallucination_result,
                    answer_check=answer_result,
                )

                history.append(iteration_record)

                logger.info(
                    "Self-reflection iteration completed",
                    extra={
                        "iteration": iteration,
                        "decision": decision.value,
                        "critic_score": critic_result.score,
                        "severity": critic_result.severity.value,
                        "requires_retrieval": (
                            critic_result.requires_retrieval
                        ),
                        "requires_regeneration": (
                            critic_result.requires_regeneration
                        ),
                    },
                )

                if decision == ReflectionDecision.ACCEPT:
                    return ReflectionResult(
                        status=ReflectionStatus.ACCEPTED,
                        final_answer=current_answer,
                        iterations=tuple(history),
                        final_critic=critic_result,
                        total_iterations=iteration,
                    )

                if (
                    decision == ReflectionDecision.RETRIEVE
                    and retrieve is not None
                    and self.config.allow_additional_retrieval
                ):
                    current_evidence = list(
                        self._retrieve(
                            retrieve,
                            query,
                            current_evidence,
                            gap_result,
                            retrieval_result,
                        )
                    )

                    if (
                        generate is not None
                        and self.config.allow_regeneration
                    ):
                        current_answer = generate(
                            query,
                            current_evidence,
                            current_answer,
                            critic_result,
                        )

                    continue

                if (
                    decision == ReflectionDecision.REGENERATE
                    and generate is not None
                    and self.config.allow_regeneration
                ):
                    current_answer = generate(
                        query,
                        current_evidence,
                        current_answer,
                        critic_result,
                    )

                    continue

                if critic_result.requires_retrieval:
                    return ReflectionResult(
                        status=ReflectionStatus.RETRIEVAL_REQUIRED,
                        final_answer=current_answer,
                        iterations=tuple(history),
                        final_critic=critic_result,
                        total_iterations=iteration,
                    )

                if critic_result.requires_regeneration:
                    return ReflectionResult(
                        status=ReflectionStatus.REGENERATION_REQUIRED,
                        final_answer=current_answer,
                        iterations=tuple(history),
                        final_critic=critic_result,
                        total_iterations=iteration,
                    )

            except Exception:
                logger.exception(
                    "Self-reflection iteration failed",
                    extra={"iteration": iteration},
                )

                return ReflectionResult(
                    status=ReflectionStatus.FAILED,
                    final_answer=current_answer,
                    iterations=tuple(history),
                    final_critic=(
                        history[-1].critic
                        if history
                        else None
                    ),
                    total_iterations=iteration,
                    metadata={
                        "error": "reflection_iteration_failed",
                    },
                )

        final_critic = history[-1].critic if history else None

        return ReflectionResult(
            status=ReflectionStatus.MAX_ITERATIONS,
            final_answer=current_answer,
            iterations=tuple(history),
            final_critic=final_critic,
            total_iterations=len(history),
        )

    def _decide(
        self,
        critic: CriticResult,
        iteration: int,
    ) -> ReflectionDecision:
        if critic.accepted:
            return ReflectionDecision.ACCEPT

        if (
            self.config.stop_on_critical
            and critic.severity == CriticSeverity.CRITICAL
        ):
            if critic.requires_retrieval:
                return ReflectionDecision.RETRIEVE

            if critic.requires_regeneration:
                return ReflectionDecision.REGENERATE

            return ReflectionDecision.STOP

        if critic.requires_retrieval:
            if self.config.allow_additional_retrieval:
                return ReflectionDecision.RETRIEVE

        if critic.requires_regeneration:
            if self.config.allow_regeneration:
                return ReflectionDecision.REGENERATE

        if iteration >= self.config.max_iterations:
            return ReflectionDecision.STOP

        return ReflectionDecision.STOP

    def _retrieve(
        self,
        retrieve: RetrieveFn,
        query: str,
        existing: Sequence[Any],
        gaps: GapDetectionResult,
        retrieval: RetrievalCheckResult,
    ) -> Sequence[Any]:
        queries = list(
            retrieval.recommended_queries
        )

        for gap in gaps.gaps:
            if gap.query_hint:
                queries.append(gap.query_hint)

        queries = list(
            dict.fromkeys(
                query.strip()
                for query in queries
                if query and query.strip()
            )
        )

        if not queries:
            queries = [query]

        try:
            return retrieve(
                query,
                existing,
                queries,
            )
        except TypeError:
            # Compatibility fallback for simpler retriever callbacks.
            return retrieve(query, existing, [query])

    @staticmethod
    def _answer_text(answer: Any) -> str:
        if answer is None:
            return ""

        if isinstance(answer, str):
            return answer

        if isinstance(answer, Mapping):
            for key in (
                "answer",
                "content",
                "text",
                "response",
            ):
                value = answer.get(key)
                if value is not None:
                    return str(value)

        for attr in (
            "answer",
            "content",
            "text",
            "response",
        ):
            value = getattr(answer, attr, None)
            if value is not None:
                return str(value)

        return str(answer)

