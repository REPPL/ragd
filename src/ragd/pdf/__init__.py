"""PDF processing module for ragd.

This module provides:
- PDF quality detection for intelligent pipeline routing
- PDF processors (PyMuPDF, Docling) for text extraction
- Pipeline factory for automatic processor selection
"""

from __future__ import annotations

from ragd.pdf.factory import (
    PDFPipelineFactory,
    PipelineType,
    extract_pdf,
    get_factory,
)
from ragd.pdf.processor import (
    ExtractedContent,
    ExtractedTable,
    PDFProcessor,
    PyMuPDFProcessor,
)
from ragd.pdf.quality import (
    PDFQuality,
    PDFQualityDetector,
    QualityAssessment,
)

__all__ = [
    # Quality detection
    "PDFQuality",
    "PDFQualityDetector",
    "QualityAssessment",
    # Processors
    "PDFProcessor",
    "PyMuPDFProcessor",
    "ExtractedContent",
    "ExtractedTable",
    # Factory
    "PDFPipelineFactory",
    "PipelineType",
    "extract_pdf",
    "get_factory",
]
