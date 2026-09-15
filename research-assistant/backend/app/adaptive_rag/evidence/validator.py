from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from .collector import EvidenceItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EvidenceValidationResult:
    """
    Result of structural evidence validation.
    """

    valid: bool
    accepted: tuple[EvidenceItem, ...]
    rejected: tuple[EvidenceItem, ...]
    errors: tuple[str, ...]

    @property
    def acceptance_rate(self) -> float:
        total = len(self.accepted) + len(self.rejected)

        if total == 0:
            return 0.0

        return len(self.accepted) / total


class EvidenceValidator:
    """
    Validates evidence before scoring.

    Validation is intentionally deterministic and does not use an LLM.
    """

    def __init__(
        self,
        *,
        min_score: float = 0.0,
        min_content_length: int = 10,
        require_identifier: bool = True,
        require_source: bool = False,
    ) -> None:
        self.min_score = min_score
        self.min_content_length = min_content_length
        self.require_identifier = require_identifier
        self.require_source = require_source

    def validate(
        self,
        evidence: Iterable[EvidenceItem],
    ) -> EvidenceValidationResult:
        accepted: list[EvidenceItem] = []
        rejected: list[EvidenceItem] = []
        errors: list[str] = []

        for item in evidence:
            item_errors = self._validate_item(item)

            if item_errors:
                rejected.append(item)

                errors.extend(
                    f"{item.evidence_id}: {error}"
                    for error in item_errors
                )
            else:
                accepted.append(item)

        return EvidenceValidationResult(
            valid=not errors,
            accepted=tuple(accepted),
            rejected=tuple(rejected),
            errors=tuple(errors),
        )

    def _validate_item(
        self,
        item: EvidenceItem,
    ) -> list[str]:
        errors: list[str] = []

        if self.require_identifier and not item.evidence_id:
            errors.append("missing evidence identifier")

        if not item.content.strip():
            errors.append("empty content")

        if len(item.content.strip()) < self.min_content_length:
            errors.append("content below minimum length")

        if item.score < self.min_score:
            errors.append("score below minimum threshold")

        if self.require_source and not (
            item.source or item.document_id
        ):
            errors.append("missing source")

        if item.rank < 0:
            errors.append("negative rank")

        return errors

    @staticmethod
    def validate_single(
        item: EvidenceItem,
    ) -> bool:
        """
        Lightweight convenience validation.
        """

        if not item.evidence_id:
            return False

        if not item.content.strip():
            return False

        if item.rank < 0:
            return False

        return True