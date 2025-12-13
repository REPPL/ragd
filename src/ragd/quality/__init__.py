"""Extraction quality scoring for ragd.

Provides quality assessment metrics for document extraction.
"""

from ragd.quality.metrics import (
    QualityMetrics,
    compute_character_quality,
    compute_completeness,
    compute_image_handling,
    compute_structure_score,
    compute_table_handling,
)
from ragd.quality.scorer import (
    QualityScorer,
    score_document,
    score_extraction,
)

__all__ = [
    # Metrics
    "QualityMetrics",
    "compute_completeness",
    "compute_character_quality",
    "compute_structure_score",
    "compute_image_handling",
    "compute_table_handling",
    # Scorer
    "QualityScorer",
    "score_document",
    "score_extraction",
]
