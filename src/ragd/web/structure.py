"""Structure preservation for HTML documents.

This module implements F-039: Advanced HTML Processing, providing
structure preservation for HTML documents including:
- Heading hierarchy extraction
- Table-to-Markdown conversion
- List structure preservation
- Code block handling
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    from selectolax.parser import HTMLParser as SelectolaxParser

    SELECTOLAX_AVAILABLE = True
except ImportError:
    SELECTOLAX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


@dataclass
class HeadingInfo:
    """Information about a heading in the document."""

    level: int  # 1-6
    text: str
    id: str | None = None


@dataclass
class TableInfo:
    """Information about a table in the document."""

    markdown: str
    rows: int = 0
    cols: int = 0
    has_header: bool = True


@dataclass
class ListInfo:
    """Information about a list in the document."""

    markdown: str
    list_type: str  # "ordered" or "unordered"
    items: int = 0


@dataclass
class CodeBlockInfo:
    """Information about a code block in the document."""

    code: str
    language: str | None = None


@dataclass
class HTMLStructure:
    """Preserved structure from HTML document.

    Contains structural elements converted to Markdown format
    for better RAG processing.
    """

    headings: list[HeadingInfo] = field(default_factory=list)
    tables: list[TableInfo] = field(default_factory=list)
    lists: list[ListInfo] = field(default_factory=list)
    code_blocks: list[CodeBlockInfo] = field(default_factory=list)

    def get_heading_outline(self) -> str:
        """Get document outline from headings.

        Returns:
            Markdown-formatted outline with indentation
        """
        lines = []
        for h in self.headings:
            indent = "  " * (h.level - 1)
            lines.append(f"{indent}- {h.text}")
        return "\n".join(lines)

    def get_all_tables_markdown(self) -> str:
        """Get all tables as Markdown.

        Returns:
            All tables joined with newlines
        """
        return "\n\n".join(t.markdown for t in self.tables)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "headings": [
                {"level": h.level, "text": h.text, "id": h.id}
                for h in self.headings
            ],
            "tables_count": len(self.tables),
            "lists_count": len(self.lists),
            "code_blocks_count": len(self.code_blocks),
        }


def extract_structure(html: str) -> HTMLStructure:
    """Extract structure from HTML document.

    Uses selectolax if available, falls back to BeautifulSoup.

    Args:
        html: HTML content

    Returns:
        HTMLStructure with preserved structural elements
    """
    if SELECTOLAX_AVAILABLE:
        return _extract_with_selectolax(html)
    elif BEAUTIFULSOUP_AVAILABLE:
        return _extract_with_beautifulsoup(html)
    else:
        return HTMLStructure()


def _extract_with_selectolax(html: str) -> HTMLStructure:
    """Extract structure using selectolax."""
    tree = SelectolaxParser(html)
    structure = HTMLStructure()

    # Extract headings
    for level in range(1, 7):
        for h in tree.css(f"h{level}"):
            text = h.text(strip=True)
            if text:
                structure.headings.append(HeadingInfo(
                    level=level,
                    text=text,
                    id=h.attributes.get("id"),
                ))

    # Sort headings by document order
    # selectolax preserves order, so headings are already in order

    # Extract tables
    for table in tree.css("table"):
        table_info = _convert_table_to_markdown_selectolax(table)
        if table_info.markdown:
            structure.tables.append(table_info)

    # Extract lists
    for ul in tree.css("ul"):
        list_info = _convert_list_to_markdown_selectolax(ul, "unordered")
        if list_info.markdown:
            structure.lists.append(list_info)

    for ol in tree.css("ol"):
        list_info = _convert_list_to_markdown_selectolax(ol, "ordered")
        if list_info.markdown:
            structure.lists.append(list_info)

    # Extract code blocks
    for pre in tree.css("pre"):
        code_tag = pre.css_first("code")
        if code_tag:
            code = code_tag.text()
            language = None
            # Try to detect language from class
            class_attr = code_tag.attributes.get("class", "")
            lang_match = re.search(r"language-(\w+)", class_attr)
            if lang_match:
                language = lang_match.group(1)
            structure.code_blocks.append(CodeBlockInfo(code=code, language=language))
        else:
            # Pre without code tag
            structure.code_blocks.append(CodeBlockInfo(code=pre.text()))

    return structure


def _extract_with_beautifulsoup(html: str) -> HTMLStructure:
    """Extract structure using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    structure = HTMLStructure()

    # Extract headings
    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            text = h.get_text(strip=True)
            if text:
                structure.headings.append(HeadingInfo(
                    level=level,
                    text=text,
                    id=h.get("id"),
                ))

    # Extract tables
    for table in soup.find_all("table"):
        table_info = _convert_table_to_markdown_bs(table)
        if table_info.markdown:
            structure.tables.append(table_info)

    # Extract lists
    for ul in soup.find_all("ul"):
        list_info = _convert_list_to_markdown_bs(ul, "unordered")
        if list_info.markdown:
            structure.lists.append(list_info)

    for ol in soup.find_all("ol"):
        list_info = _convert_list_to_markdown_bs(ol, "ordered")
        if list_info.markdown:
            structure.lists.append(list_info)

    # Extract code blocks
    for pre in soup.find_all("pre"):
        code_tag = pre.find("code")
        if code_tag:
            code = code_tag.get_text()
            language = None
            class_attr = " ".join(code_tag.get("class", []))
            lang_match = re.search(r"language-(\w+)", class_attr)
            if lang_match:
                language = lang_match.group(1)
            structure.code_blocks.append(CodeBlockInfo(code=code, language=language))
        else:
            structure.code_blocks.append(CodeBlockInfo(code=pre.get_text()))

    return structure


def _convert_table_to_markdown_selectolax(table: Any) -> TableInfo:
    """Convert HTML table to Markdown using selectolax.

    Args:
        table: selectolax table node

    Returns:
        TableInfo with Markdown representation
    """
    rows = []
    max_cols = 0

    # Extract header row
    thead = table.css_first("thead")
    if thead:
        header_row = []
        for th in thead.css("th"):
            header_row.append(_clean_cell_text(th.text(strip=True)))
        if header_row:
            rows.append(header_row)
            max_cols = max(max_cols, len(header_row))

    # Extract body rows
    tbody = table.css_first("tbody") or table
    for tr in tbody.css("tr"):
        row = []
        for cell in tr.css("td, th"):
            row.append(_clean_cell_text(cell.text(strip=True)))
        if row:
            rows.append(row)
            max_cols = max(max_cols, len(row))

    if not rows:
        return TableInfo(markdown="", rows=0, cols=0, has_header=False)

    # Normalise row lengths
    for row in rows:
        while len(row) < max_cols:
            row.append("")

    # Generate Markdown
    md_lines = []

    # First row (header or data)
    md_lines.append("| " + " | ".join(rows[0]) + " |")
    md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    # Remaining rows
    for row in rows[1:]:
        md_lines.append("| " + " | ".join(row) + " |")

    return TableInfo(
        markdown="\n".join(md_lines),
        rows=len(rows),
        cols=max_cols,
        has_header=thead is not None,
    )


def _convert_table_to_markdown_bs(table: Any) -> TableInfo:
    """Convert HTML table to Markdown using BeautifulSoup.

    Args:
        table: BeautifulSoup table element

    Returns:
        TableInfo with Markdown representation
    """
    rows = []
    max_cols = 0

    # Extract header row
    thead = table.find("thead")
    if thead:
        header_row = []
        for th in thead.find_all("th"):
            header_row.append(_clean_cell_text(th.get_text(strip=True)))
        if header_row:
            rows.append(header_row)
            max_cols = max(max_cols, len(header_row))

    # Extract body rows
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        row = []
        for cell in tr.find_all(["td", "th"]):
            row.append(_clean_cell_text(cell.get_text(strip=True)))
        if row:
            rows.append(row)
            max_cols = max(max_cols, len(row))

    if not rows:
        return TableInfo(markdown="", rows=0, cols=0, has_header=False)

    # Normalise row lengths
    for row in rows:
        while len(row) < max_cols:
            row.append("")

    # Generate Markdown
    md_lines = []

    # First row (header or data)
    md_lines.append("| " + " | ".join(rows[0]) + " |")
    md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    # Remaining rows
    for row in rows[1:]:
        md_lines.append("| " + " | ".join(row) + " |")

    return TableInfo(
        markdown="\n".join(md_lines),
        rows=len(rows),
        cols=max_cols,
        has_header=thead is not None,
    )


def _convert_list_to_markdown_selectolax(list_elem: Any, list_type: str) -> ListInfo:
    """Convert HTML list to Markdown using selectolax.

    Args:
        list_elem: selectolax list node (ul or ol)
        list_type: "ordered" or "unordered"

    Returns:
        ListInfo with Markdown representation
    """
    lines = []
    item_count = 0

    for idx, li in enumerate(list_elem.css("li"), start=1):
        text = li.text(strip=True)
        if text:
            item_count += 1
            prefix = f"{idx}. " if list_type == "ordered" else "- "
            lines.append(prefix + text)

    return ListInfo(
        markdown="\n".join(lines),
        list_type=list_type,
        items=item_count,
    )


def _convert_list_to_markdown_bs(list_elem: Any, list_type: str) -> ListInfo:
    """Convert HTML list to Markdown using BeautifulSoup.

    Args:
        list_elem: BeautifulSoup list element (ul or ol)
        list_type: "ordered" or "unordered"

    Returns:
        ListInfo with Markdown representation
    """
    lines = []
    item_count = 0

    for idx, li in enumerate(list_elem.find_all("li", recursive=False), start=1):
        text = li.get_text(strip=True)
        if text:
            item_count += 1
            prefix = f"{idx}. " if list_type == "ordered" else "- "
            lines.append(prefix + text)

    return ListInfo(
        markdown="\n".join(lines),
        list_type=list_type,
        items=item_count,
    )


def _clean_cell_text(text: str) -> str:
    """Clean table cell text for Markdown.

    Args:
        text: Raw cell text

    Returns:
        Cleaned text safe for Markdown tables
    """
    # Replace pipe characters
    text = text.replace("|", "\\|")
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_text_with_structure(html: str) -> str:
    """Extract text while preserving structure as Markdown.

    This combines content extraction with structure preservation,
    converting tables and lists to Markdown inline.

    Args:
        html: HTML content

    Returns:
        Text with Markdown-formatted structure
    """
    structure = extract_structure(html)

    # Start with heading outline
    parts = []

    if structure.headings:
        parts.append("## Document Outline\n")
        parts.append(structure.get_heading_outline())
        parts.append("")

    if structure.tables:
        parts.append("## Tables\n")
        parts.append(structure.get_all_tables_markdown())
        parts.append("")

    # Extract main text using parser
    if SELECTOLAX_AVAILABLE:
        tree = SelectolaxParser(html)
        # Remove unwanted elements
        for tag in tree.css("script, style, nav, footer, aside"):
            tag.decompose()
        body = tree.css_first("article") or tree.css_first("main") or tree.css_first("body")
        if body:
            parts.append(body.text(strip=True))
    elif BEAUTIFULSOUP_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()
        body = soup.find("article") or soup.find("main") or soup.body
        if body:
            parts.append(body.get_text(strip=True))

    return "\n\n".join(parts)
