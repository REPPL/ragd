"""Citation formatting and validation for ragd search results.

Provides citation generation in multiple formats and validation
to detect potential hallucinations.
"""

from ragd.citation.citation import Citation, CitationStyle
from ragd.citation.extractor import ExtractedCitation, extract_citation_markers
from ragd.citation.formatter import (
    CitationFormatter,
    format_citation,
    format_citations,
    get_formatter,
)
from ragd.citation.validator import (
    CitationValidation,
    CitationValidator,
    ValidationMode,
    ValidationReport,
    ValidationResult,
    validate_citations,
)

__all__ = [
    # Core citation types
    "Citation",
    "CitationStyle",
    # Formatting
    "CitationFormatter",
    "format_citation",
    "format_citations",
    "get_formatter",
    # Extraction
    "ExtractedCitation",
    "extract_citation_markers",
    # Validation
    "CitationValidation",
    "CitationValidator",
    "ValidationMode",
    "ValidationReport",
    "ValidationResult",
    "validate_citations",
]
