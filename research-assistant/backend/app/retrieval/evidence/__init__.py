"""
Evidence collection and evaluation for the retrieval pipeline.

The evidence layer is responsible for:

- Collecting retrieved/reranked results
- Scoring evidence quality
- Measuring evidence coverage
- Preserving provenance
- Producing a normalized evidence representation for downstream RAG
"""

from .collector import EvidenceCollector
from .coverage import EvidenceCoverage, EvidenceCoverageCalculator
from .provenance import EvidenceProvenance, ProvenanceBuilder
from .scorer import EvidenceScore, EvidenceScorer

__all__ = [
    "EvidenceCollector",
    "EvidenceCoverage",
    "EvidenceCoverageCalculator",
    "EvidenceProvenance",
    "ProvenanceBuilder",
    "EvidenceScore",
    "EvidenceScorer",
]