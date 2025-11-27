"""Citation formatting for ragd search results.

Provides citation generation in multiple academic and technical formats.
"""

from ragd.citation.citation import Citation, CitationStyle
from ragd.citation.formatter import (
    CitationFormatter,
    format_citation,
    format_citations,
    get_formatter,
)

__all__ = [
    "Citation",
    "CitationStyle",
    "CitationFormatter",
    "format_citation",
    "format_citations",
    "get_formatter",
]
