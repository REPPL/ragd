"""Privacy module for ragd.

This module provides PII detection and handling capabilities:
- Detection using Presidio, spaCy, or regex patterns
- PII reporting for documents
- Redaction utilities

The module is designed to work offline with local models.
"""

from ragd.privacy.pii import (
    PIIDetector,
    PIIEngine,
    PIIEntity,
    PIIEntityType,
    PIIReport,
    PIIResult,
    is_presidio_available,
    is_spacy_available,
    redact_pii,
)

__all__ = [
    "PIIDetector",
    "PIIEngine",
    "PIIEntity",
    "PIIEntityType",
    "PIIReport",
    "PIIResult",
    "is_presidio_available",
    "is_spacy_available",
    "redact_pii",
]
