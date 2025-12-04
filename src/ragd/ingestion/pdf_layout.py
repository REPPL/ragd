"""PDF layout intelligence for ragd (F-099).

Provides enhanced PDF extraction with:
- Multi-column detection and proper reading order
- Form field extraction
- Annotation preservation
- Table structure detection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


logger = logging.getLogger(__name__)


@dataclass
class LayoutConfig:
    """Configuration for PDF layout analysis."""

    layout_analysis: bool = True
    extract_forms: bool = True
    extract_annotations: bool = True
    preserve_tables: bool = True
    column_threshold: float = 0.3  # Gap ratio to detect columns


@dataclass
class LayoutRegion:
    """A rectangular region in a PDF page."""

    x0: float
    y0: float
    x1: float
    y1: float
    text: str = ""
    region_type: str = "text"  # text, form, annotation, table

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class PageLayout:
    """Layout analysis for a PDF page."""

    page_number: int
    width: float
    height: float
    regions: list[LayoutRegion] = field(default_factory=list)
    columns: int = 1
    has_tables: bool = False
    has_forms: bool = False
    has_annotations: bool = False


@dataclass
class PDFLayoutResult:
    """Result of PDF layout analysis."""

    text: str
    pages: list[PageLayout]
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


def detect_columns(blocks: list[dict], page_width: float, threshold: float = 0.3) -> int:
    """Detect number of columns in page layout.

    Args:
        blocks: List of text blocks with bounding boxes
        page_width: Width of the page
        threshold: Minimum gap ratio to detect column boundary

    Returns:
        Number of detected columns (1-3)
    """
    if not blocks:
        return 1

    # Get x-coordinates of block boundaries
    x_centers = []
    for block in blocks:
        if "bbox" in block:
            x0, y0, x1, y1 = block["bbox"]
            center_x = (x0 + x1) / 2
            x_centers.append(center_x)

    if not x_centers:
        return 1

    # Sort by x-coordinate
    x_centers.sort()

    # Look for gaps indicating column boundaries
    gaps = []
    for i in range(len(x_centers) - 1):
        gap = x_centers[i + 1] - x_centers[i]
        if gap > page_width * threshold:
            gaps.append((i, gap))

    # Determine column count
    if len(gaps) >= 2:
        return 3
    elif len(gaps) == 1:
        return 2
    else:
        return 1


def extract_form_fields(page: fitz.Page) -> list[dict[str, Any]]:
    """Extract form fields from a PDF page.

    Args:
        page: PyMuPDF page object

    Returns:
        List of form field dictionaries
    """
    fields = []

    for widget in page.widgets():
        field_data = {
            "type": widget.field_type_string,
            "name": widget.field_name,
            "value": widget.field_value,
            "rect": list(widget.rect),
        }
        fields.append(field_data)

    return fields


def extract_annotations(page: fitz.Page) -> list[dict[str, Any]]:
    """Extract annotations from a PDF page.

    Args:
        page: PyMuPDF page object

    Returns:
        List of annotation dictionaries
    """
    annotations = []

    for annot in page.annots():
        if annot is None:
            continue

        annot_data = {
            "type": annot.type[1],  # Type name
            "rect": list(annot.rect),
            "content": annot.info.get("content", ""),
            "title": annot.info.get("title", ""),
        }
        annotations.append(annot_data)

    return annotations


def detect_tables(page: fitz.Page) -> list[dict[str, Any]]:
    """Detect table structures in a PDF page.

    Args:
        page: PyMuPDF page object

    Returns:
        List of detected table regions
    """
    tables = []

    # Use PyMuPDF's table detection if available (fitz 1.22+)
    try:
        tabs = page.find_tables()
        for table in tabs:
            table_data = {
                "bbox": list(table.bbox),
                "rows": table.row_count,
                "cols": table.col_count,
            }
            tables.append(table_data)
    except AttributeError:
        # Older PyMuPDF version - basic detection via line analysis
        pass

    return tables


def reorder_by_reading_order(blocks: list[dict], columns: int) -> list[dict]:
    """Reorder text blocks by reading order.

    For multi-column layouts, reads top-to-bottom within each column,
    then left-to-right across columns.

    Args:
        blocks: List of text blocks
        columns: Number of detected columns

    Returns:
        Reordered list of blocks
    """
    if columns == 1 or not blocks:
        # Single column - sort by y-coordinate
        return sorted(blocks, key=lambda b: b.get("bbox", (0, 0, 0, 0))[1])

    # Get page width from blocks
    all_x0 = [b["bbox"][0] for b in blocks if "bbox" in b]
    all_x1 = [b["bbox"][2] for b in blocks if "bbox" in b]

    if not all_x0:
        return blocks

    min_x = min(all_x0)
    max_x = max(all_x1)
    width = max_x - min_x

    if columns == 2:
        mid = min_x + width / 2
        left = [b for b in blocks if "bbox" in b and b["bbox"][0] < mid]
        right = [b for b in blocks if "bbox" in b and b["bbox"][0] >= mid]

        # Sort each column top-to-bottom
        left.sort(key=lambda b: b["bbox"][1])
        right.sort(key=lambda b: b["bbox"][1])

        return left + right

    elif columns == 3:
        third = width / 3
        left = [b for b in blocks if "bbox" in b and b["bbox"][0] < min_x + third]
        middle = [b for b in blocks if "bbox" in b and min_x + third <= b["bbox"][0] < min_x + 2 * third]
        right = [b for b in blocks if "bbox" in b and b["bbox"][0] >= min_x + 2 * third]

        left.sort(key=lambda b: b["bbox"][1])
        middle.sort(key=lambda b: b["bbox"][1])
        right.sort(key=lambda b: b["bbox"][1])

        return left + middle + right

    return blocks


def analyse_pdf_layout(
    path: Path,
    config: LayoutConfig | None = None,
) -> PDFLayoutResult:
    """Analyse PDF layout and extract text with intelligence.

    Args:
        path: Path to PDF file
        config: Layout analysis configuration

    Returns:
        PDFLayoutResult with text and layout information
    """
    if config is None:
        config = LayoutConfig()

    try:
        doc = fitz.open(path)
    except Exception as e:
        return PDFLayoutResult(
            text="",
            pages=[],
            success=False,
            error=str(e),
        )

    pages: list[PageLayout] = []
    all_text_parts: list[str] = []

    for page_num, page in enumerate(doc):
        page_layout = PageLayout(
            page_number=page_num + 1,
            width=page.rect.width,
            height=page.rect.height,
        )

        # Get text blocks
        blocks = page.get_text("dict")["blocks"]
        text_blocks = [b for b in blocks if b.get("type") == 0]  # Text blocks only

        # Detect columns
        if config.layout_analysis:
            page_layout.columns = detect_columns(
                text_blocks,
                page.rect.width,
                config.column_threshold,
            )

            # Reorder blocks by reading order
            text_blocks = reorder_by_reading_order(text_blocks, page_layout.columns)

        # Extract text from blocks
        page_text_parts = []
        for block in text_blocks:
            block_text = ""
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                if line_text.strip():
                    block_text += line_text + "\n"

            if block_text.strip():
                page_text_parts.append(block_text.strip())

                # Create region
                if "bbox" in block:
                    region = LayoutRegion(
                        x0=block["bbox"][0],
                        y0=block["bbox"][1],
                        x1=block["bbox"][2],
                        y1=block["bbox"][3],
                        text=block_text.strip(),
                        region_type="text",
                    )
                    page_layout.regions.append(region)

        # Extract form fields
        if config.extract_forms:
            fields = extract_form_fields(page)
            if fields:
                page_layout.has_forms = True
                for field in fields:
                    if field.get("value"):
                        page_text_parts.append(
                            f"[Form Field: {field.get('name', 'unknown')}] {field['value']}"
                        )

        # Extract annotations
        if config.extract_annotations:
            annotations = extract_annotations(page)
            if annotations:
                page_layout.has_annotations = True
                for annot in annotations:
                    if annot.get("content"):
                        page_text_parts.append(
                            f"[{annot.get('type', 'Note')}] {annot['content']}"
                        )

        # Detect tables
        if config.preserve_tables:
            tables = detect_tables(page)
            if tables:
                page_layout.has_tables = True

        # Combine page text
        page_text = "\n\n".join(page_text_parts)
        if page_text.strip():
            all_text_parts.append(page_text)

        pages.append(page_layout)

    doc.close()

    # Build metadata
    metadata = {
        "source": str(path),
        "format": "pdf",
        "pages": len(pages),
        "columns_detected": max((p.columns for p in pages), default=1),
        "has_forms": any(p.has_forms for p in pages),
        "has_annotations": any(p.has_annotations for p in pages),
        "has_tables": any(p.has_tables for p in pages),
    }

    return PDFLayoutResult(
        text="\n\n---\n\n".join(all_text_parts),
        pages=pages,
        metadata=metadata,
        success=True,
    )


class PDFLayoutExtractor:
    """PDF extractor with layout intelligence (F-099).

    Provides enhanced extraction for complex PDF layouts:
    - Multi-column reading order
    - Form field extraction
    - Annotation preservation
    - Table detection
    """

    def __init__(self, config: LayoutConfig | None = None) -> None:
        """Initialise layout-aware PDF extractor.

        Args:
            config: Layout analysis configuration
        """
        self.config = config or LayoutConfig()

    def extract(self, path: Path):
        """Extract text from PDF with layout intelligence.

        Args:
            path: Path to PDF file

        Returns:
            ExtractionResult with text and layout metadata
        """
        from ragd.ingestion.extractor import ExtractionResult

        result = analyse_pdf_layout(path, self.config)

        return ExtractionResult(
            text=result.text,
            metadata=result.metadata,
            pages=result.metadata.get("pages"),
            extraction_method="pymupdf_layout",
            success=result.success,
            error=result.error,
        )
