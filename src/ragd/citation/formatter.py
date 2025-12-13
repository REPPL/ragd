"""Citation formatters for various academic and technical styles.

Provides formatters for APA, MLA, Chicago, BibTeX, and other formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from ragd.citation.citation import Citation, CitationStyle


class CitationFormatter(ABC):
    """Abstract base class for citation formatters."""

    @abstractmethod
    def format(self, citation: Citation) -> str:
        """Format a single citation.

        Args:
            citation: Citation to format

        Returns:
            Formatted citation string
        """
        pass

    def format_many(self, citations: list[Citation]) -> list[str]:
        """Format multiple citations.

        Args:
            citations: List of citations

        Returns:
            List of formatted citation strings
        """
        return [self.format(c) for c in citations]


class APAFormatter(CitationFormatter):
    """APA 7th edition citation formatter.

    Format: Author (Year). Title. Source. Retrieved Date, from Location.
    """

    def format(self, citation: Citation) -> str:
        parts = []

        # Author (or title if no author)
        if citation.author:
            parts.append(citation.author)
        else:
            parts.append(citation.display_title)

        # Year/date
        if citation.indexed_at:
            year = citation.indexed_at[:4]  # Extract year from ISO date
            parts[0] += f" ({year})."
        else:
            parts[0] += " (n.d.)."

        # Title (if we used author above)
        if citation.author:
            parts.append(f"*{citation.display_title}*.")

        # File type
        if citation.file_type:
            parts.append(f"[{citation.file_type.upper()}].")

        # Location
        if citation.page_number:
            parts.append(f"p. {citation.page_number}.")

        # Access date
        if citation.accessed_date:
            parts.append(f"Retrieved {_format_date_apa(citation.accessed_date)}.")

        # Source path
        if citation.file_path:
            parts.append(f"from {citation.file_path}")

        return " ".join(parts)


class MLAFormatter(CitationFormatter):
    """MLA 9th edition citation formatter.

    Format: Author. "Title." Container, Location.
    """

    def format(self, citation: Citation) -> str:
        parts = []

        # Author
        if citation.author:
            parts.append(f"{citation.author}.")
        else:
            parts.append("")

        # Title in quotes
        parts.append(f'"{citation.display_title}."')

        # File type as container
        if citation.file_type:
            parts.append(f"*{citation.file_type.upper()} Document*,")

        # Page
        if citation.page_number:
            parts.append(f"p. {citation.page_number}.")

        # Clean up empty author
        result = " ".join(parts).strip()
        if result.startswith(" "):
            result = result[1:]

        return result


class ChicagoFormatter(CitationFormatter):
    """Chicago Manual of Style (notes-bibliography) formatter.

    Format: Author, "Title" (Location, Date), page.
    """

    def format(self, citation: Citation) -> str:
        parts = []

        # Author
        if citation.author:
            parts.append(f"{citation.author},")

        # Title
        parts.append(f'"{citation.display_title}"')

        # Location and date in parentheses
        meta_parts = []
        if citation.file_type:
            meta_parts.append(citation.file_type.upper())
        if citation.indexed_at:
            meta_parts.append(citation.indexed_at[:10])  # YYYY-MM-DD
        if meta_parts:
            parts.append(f"({', '.join(meta_parts)})")

        # Page
        if citation.page_number:
            parts.append(f"{citation.page_number}.")
        else:
            parts[-1] = parts[-1].rstrip(")") + ")"
            parts.append(".")

        return " ".join(parts).replace(" .", ".").replace("..", ".")


class BibTeXFormatter(CitationFormatter):
    """BibTeX citation formatter.

    Generates @misc entries suitable for LaTeX bibliographies.
    """

    def format(self, citation: Citation) -> str:
        # Generate entry key
        key = _sanitise_key(citation.document_id or citation.filename)

        lines = [f"@misc{{{key},"]

        # Title
        lines.append(f"  title = {{{citation.display_title}}},")

        # Author
        if citation.author:
            lines.append(f"  author = {{{citation.author}}},")

        # Year
        if citation.indexed_at:
            year = citation.indexed_at[:4]
            lines.append(f"  year = {{{year}}},")

        # Note with file type
        if citation.file_type:
            lines.append(f"  note = {{{citation.file_type.upper()} document}},")

        # How published
        if citation.file_path:
            lines.append(f"  howpublished = {{Local file: {citation.file_path}}},")

        # Pages
        if citation.page_number:
            lines.append(f"  pages = {{{citation.page_number}}},")

        lines.append("}")

        return "\n".join(lines)


class InlineFormatter(CitationFormatter):
    """Simple inline citation formatter.

    Format: (filename, p. X) or (filename, chunk Y)
    """

    def format(self, citation: Citation) -> str:
        parts = [citation.filename]

        if citation.page_number:
            parts.append(f"p. {citation.page_number}")
        elif citation.chunk_index is not None:
            parts.append(f"chunk {citation.chunk_index}")

        return f"({', '.join(parts)})"


class MarkdownFormatter(CitationFormatter):
    """Markdown-friendly citation formatter.

    Format: [Title](path) - page X
    """

    def format(self, citation: Citation) -> str:
        title = citation.display_title
        path = citation.file_path or citation.filename

        parts = [f"[{title}]({path})"]

        if citation.page_number:
            parts.append(f"p. {citation.page_number}")
        elif citation.chunk_index is not None:
            parts.append(f"section {citation.chunk_index + 1}")

        return " - ".join(parts)


# Formatter registry
_FORMATTERS: dict[CitationStyle, type[CitationFormatter]] = {
    CitationStyle.APA: APAFormatter,
    CitationStyle.MLA: MLAFormatter,
    CitationStyle.CHICAGO: ChicagoFormatter,
    CitationStyle.BIBTEX: BibTeXFormatter,
    CitationStyle.INLINE: InlineFormatter,
    CitationStyle.MARKDOWN: MarkdownFormatter,
}


def get_formatter(style: CitationStyle | str) -> CitationFormatter:
    """Get a formatter for the specified style.

    Args:
        style: Citation style (enum or string)

    Returns:
        CitationFormatter instance

    Raises:
        ValueError: If style is not recognised
    """
    if isinstance(style, str):
        try:
            style = CitationStyle(style.lower())
        except ValueError:
            valid = [s.value for s in CitationStyle]
            raise ValueError(f"Unknown citation style: {style}. Valid: {valid}")

    formatter_class = _FORMATTERS.get(style)
    if formatter_class is None:
        raise ValueError(f"No formatter registered for style: {style}")

    return formatter_class()


def format_citation(
    citation: Citation,
    style: CitationStyle | str = CitationStyle.INLINE,
) -> str:
    """Format a single citation.

    Args:
        citation: Citation to format
        style: Output style

    Returns:
        Formatted citation string
    """
    formatter = get_formatter(style)
    return formatter.format(citation)


def format_citations(
    citations: list[Citation],
    style: CitationStyle | str = CitationStyle.INLINE,
) -> list[str]:
    """Format multiple citations.

    Args:
        citations: List of citations
        style: Output style

    Returns:
        List of formatted citation strings
    """
    formatter = get_formatter(style)
    return formatter.format_many(citations)


def _format_date_apa(d: date) -> str:
    """Format date in APA style (Month Day, Year).

    Args:
        d: Date to format

    Returns:
        APA-formatted date string
    """
    return d.strftime("%B %d, %Y")


def _sanitise_key(text: str) -> str:
    """Sanitise text for use as BibTeX key.

    Args:
        text: Input text

    Returns:
        Valid BibTeX key
    """
    import re

    # Keep only alphanumeric and underscores
    key = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    # Ensure starts with letter
    if key and not key[0].isalpha():
        key = "ref_" + key
    return key[:50]  # Limit length
