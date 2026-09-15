from .collector import (
    EvidenceCollector,
    EvidenceCollection,
    EvidenceItem,
)

from .validator import (
    EvidenceValidator,
    EvidenceValidationResult,
)

from .provenance import (
    ProvenanceTracker,
    ProvenanceRecord,
)

from .coverage import (
    EvidenceCoverageEvaluator,
    CoverageResult,
)

from .corroboration import (
    CorroborationEvaluator,
    CorroborationResult,
)

from .contradiction import (
    ContradictionDetector,
    ContradictionPair,
    ContradictionResult,
)

from .scorer import (
    EvidenceScorer,
    EvidenceScore,
    EvidenceAssessment,
)


__all__ = [
    "EvidenceCollector",
    "EvidenceCollection",
    "EvidenceItem",
    "EvidenceValidator",
    "EvidenceValidationResult",
    "ProvenanceTracker",
    "ProvenanceRecord",
    "EvidenceCoverageEvaluator",
    "CoverageResult",
    "CorroborationEvaluator",
    "CorroborationResult",
    "ContradictionDetector",
    "ContradictionPair",
    "ContradictionResult",
    "EvidenceScorer",
    "EvidenceScore",
    "EvidenceAssessment",
]