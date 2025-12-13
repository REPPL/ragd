"""OCR processing module for ragd.

This module provides:
- OCR engines (PaddleOCR, EasyOCR)
- OCR pipeline with automatic fallback
- Result dataclasses for OCR output
"""

from __future__ import annotations

from ragd.ocr.engine import (
    BoundingBox,
    EasyOCREngine,
    OCREngine,
    OCRResult,
    PaddleOCREngine,
    PageOCRResult,
    create_ocr_engine,
    get_available_engine,
)
from ragd.ocr.pipeline import (
    DocumentOCRResult,
    OCRConfig,
    OCRPipeline,
    calculate_weighted_confidence,
    filter_by_confidence,
)

__all__ = [
    # Data classes
    "BoundingBox",
    "OCRResult",
    "PageOCRResult",
    "DocumentOCRResult",
    # Engines
    "OCREngine",
    "PaddleOCREngine",
    "EasyOCREngine",
    # Pipeline
    "OCRConfig",
    "OCRPipeline",
    # Utilities
    "create_ocr_engine",
    "get_available_engine",
    "filter_by_confidence",
    "calculate_weighted_confidence",
]
