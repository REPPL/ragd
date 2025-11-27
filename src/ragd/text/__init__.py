"""Text normalisation and quality improvement module.

This module provides text cleaning and normalisation for extracted content,
addressing common issues in PDF and HTML extraction such as:
- Spaced letters (y o u r → your)
- Word boundary errors (abig → a big)
- Spurious line breaks
- OCR spelling errors
- HTML boilerplate content
"""

from __future__ import annotations

from ragd.text.normalise import (
    NormalisationResult,
    SourceType,
    TextNormaliser,
    normalise_text,
)

__all__ = [
    "TextNormaliser",
    "NormalisationResult",
    "SourceType",
    "normalise_text",
]
