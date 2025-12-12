# State-of-the-Art Table & Figure Extraction for RAG Systems

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

Comprehensive techniques for extracting tables, figures, and captions from documents across PDF, HTML, web archives, and ebooks for RAG knowledge bases.

## Executive Summary

Table and figure extraction is critical for RAG systems because structured data (tables) and visual content (figures) often contain the most valuable information in documents. Extracting these elements with their captions enables better retrieval, structured querying, and multi-modal search.

### Key Insights (2024-2025)

- **Docling/TableFormer achieves 97.9% cell accuracy** on complex tables (March 2025 benchmark)
- **PDFFigures 2.0 reaches 94% precision at 90% recall** for scholarly figure extraction
- **Vision-Language Models** (Claude 3.5, GPT-4V) enable end-to-end understanding without explicit extraction
- **Granite-Docling-258M** achieves TEDS-structure 0.97, outperforming larger models
- **Traditional tools (Tabula, Camelot)** score only 67-73% on complex tables

### Decision Matrix: Extraction by Document Type

| Format | Tables | Figures | Captions | Recommended Approach |
|--------|--------|---------|----------|---------------------|
| **PDF (digital, simple)** | PyMuPDF | PyMuPDF | Heuristic | Fast path |
| **PDF (digital, complex)** | Docling/TableFormer | Docling/PyMuPDF | Layout analysis | Structure-aware |
| **PDF (scanned)** | Docling + PaddleOCR | OCR regions | Spatial | OCR fallback |
| **PDF (image-heavy)** | VLM direct | ColPali | VLM generation | Vision-first |
| **HTML (static)** | selectolax/Pandas | `<figure>` parsing | `<figcaption>` | Standard parsing |
| **HTML (dynamic)** | Playwright + parsing | Playwright | Same | Render first |
| **SingleFile/MHTML** | Same as HTML | Base64 decode | Same | Archive handling |
| **EPUB** | EbookLib + BS4 | Manifest images | Chapter context | Ebook structure |

---

## 1. The Table Extraction Problem

### Why Tables Are Hard

Tables present unique challenges for document understanding:

| Challenge | Description | Impact |
|-----------|-------------|--------|
| **Spanning cells** | Rowspan/colspan merging cells | Structure ambiguity |
| **Borderless tables** | Visual alignment only, no lines | Detection difficulty |
| **Nested tables** | Tables within tables | Recursive parsing |
| **Multi-page tables** | Headers repeated across pages | Continuity tracking |
| **Rotated tables** | 90° or arbitrary rotation | Orientation detection |
| **Mixed content** | Text, numbers, images in cells | Type handling |

### Semantic vs Visual Structure

```
Visual Structure:          Semantic Structure:
┌────┬────┬────┐          <table>
│ A  │ B  │ C  │            <tr><th>A</th><th>B</th><th>C</th></tr>
├────┼────┼────┤            <tr><td>1</td><td>2</td><td>3</td></tr>
│ 1  │ 2  │ 3  │          </table>
└────┴────┴────┘
```

**Challenge:** Converting visual layout to semantic structure requires understanding:
- Which rows are headers vs data
- Cell boundaries (especially without borders)
- Reading order (left-to-right, top-to-bottom)
- Hierarchical relationships

### Caption Association Challenges

Captions can appear:
- **Above** the table/figure (common in academic papers)
- **Below** the table/figure (common in reports)
- **Inline** as part of surrounding text
- **Separate** with cross-references ("See Table 1")

---

## 2. PDF Table Extraction

### 2.1 Deep Learning Approaches

#### TableFormer (Docling)

TableFormer is IBM's transformer-based model for table structure recognition, integrated into Docling.

**Architecture:**
```
Table Region → Image Encoder → Transformer Decoder → Cell Coordinates + Structure
```

**Performance (March 2025 Benchmark):**

| Tool | Complex Table Accuracy | Simple Table Accuracy |
|------|------------------------|----------------------|
| **Docling/TableFormer** | **97.9%** | 99%+ |
| Unstructured | 75% | 100% |
| LlamaParse | ~90% | 98% |
| Tabula | 67.9% | 85% |
| Camelot | 73.0% | 90% |

**Source:** [Procycons PDF Benchmark 2025](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/)

#### HTTD (Hierarchical Transformer for Table Detection)

Published January 2025, HTTD uses Swin Transformers for hierarchical feature extraction:

**Innovations:**
- Contrastive denoising for better cell boundary detection
- Mixed query selection for handling diverse table styles
- Look-forward-twice refinement for improved accuracy

**Source:** [MDPI Mathematics 2025](https://www.mdpi.com/2227-7390/13/2/266)

#### PP-PicoDet + PaddleOCR

For scanned documents, PaddleOCR's pipeline achieves 96.4% accuracy:

```
Scanned PDF → PP-PicoDet (Layout) → Table Region → PaddleOCR (Recognition) → Structure
```

**Optimisations:**
- Watermark removal preprocessing
- Multi-task learning for layout + recognition
- GPU acceleration

**Source:** [BDICN 2025](https://dl.acm.org/doi/full/10.1145/3727353.3727391)

### 2.2 Tool Comparison

| Tool | Approach | Best For | Limitations |
|------|----------|----------|-------------|
| **Docling** | Deep learning (TableFormer) | Complex layouts, nested tables | Requires model download |
| **Tabula** | Rule-based (line detection) | Simple bordered tables | Fails on borderless |
| **Camelot** | Rule-based + stream | Medium complexity | Struggles with images |
| **pdfplumber** | Coordinate-based | Programmatic extraction | Manual configuration |
| **Unstructured** | Hybrid | General purpose | Less accurate on complex |
| **LlamaParse** | Cloud LLM | Fast, simple API | Cost, privacy |

### 2.3 Vision-Language Models

VLMs can understand tables directly from images without explicit extraction:

```python
# Claude 3.5 table understanding
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "data": table_image_b64}},
            {"type": "text", "text": "Extract this table as Markdown with all data preserved."}
        ]
    }]
)
```

**2025 Benchmarks:**

| Model | Table Understanding | Speed | Cost |
|-------|---------------------|-------|------|
| Claude 3.5 Sonnet | Best-in-class | ~1.8s | $$ |
| GPT-4V | Good, occasional JSON issues | ~1s | $$ |
| Granite-Docling-258M | TEDS 0.97 | 0.35s/page | Free (local) |

**Source:** [Nanonets VLM Comparison](https://nanonets.com/blog/vision-language-model-vlm-for-data-extraction/)

### 2.4 Current ragd Implementation

ragd uses Docling with TableFormer for PDF table extraction:

**File:** `src/ragd/pdf/docling.py`

```python
@dataclass
class ExtractedTable:
    """Table extracted from document."""
    page_number: int
    table_index: int
    markdown: str          # Table as Markdown
    rows: int
    cols: int
    confidence: float = 1.0

class DoclingProcessor:
    def extract(self, pdf_path: Path) -> ExtractedContent:
        # Returns ExtractedContent with text, pages, tables list, metadata
        ...
```

**Capabilities:**
- ✅ TableFormer 97.9% accuracy
- ✅ Markdown output for chunking
- ✅ Page number and index tracking
- ⚠️ Caption extraction (via Docling API)
- ❌ Table-caption linking

---

## 3. Figure Extraction from PDFs

### 3.1 Detection Approaches

#### PDFFigures 2.0 (Allen AI)

The gold standard for scholarly figure extraction:

**Performance:** 94% precision at 90% recall

**Approach:**
1. Analyse page structure (detect captions, graphical elements, body text)
2. Identify figure regions by reasoning about empty space
3. Associate captions with figures via spatial proximity

```bash
# Installation
pip install pdffigures2

# Usage
pdffigures2 input.pdf -o output/ -d output/figures/
```

**Output:** JSON with figure bounding boxes, captions, and extracted images.

**Source:** [PDFFigures 2.0 GitHub](https://github.com/allenai/pdffigures2)

#### GROBID

Machine learning framework for scholarly document parsing (used by Semantic Scholar, ResearchGate):

**Figure-related capabilities:**
- 68 label types including figure captions
- Full-text structure extraction
- Reference linking

```python
from grobid_client.grobid_client import GrobidClient

client = GrobidClient(config_path="./config.json")
client.process("processFulltextDocument", input_path, output_path)
```

**Source:** [GROBID GitHub](https://github.com/kermitt2/grobid)

#### DocLayNet (Docling)

IBM's layout analysis model identifies figure regions:

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(pdf_path)

for element in result.document.iterate_items():
    if element.label == "figure":
        print(f"Figure at page {element.prov.page_no}")
        print(f"Bounding box: {element.prov.bbox}")
```

### 3.2 Caption Association

#### Spatial Proximity Algorithm

```python
def associate_captions(figures: list, captions: list) -> list:
    """Associate captions with figures based on proximity."""
    associations = []

    for fig in figures:
        # Find closest caption (above or below)
        best_caption = None
        min_distance = float('inf')

        for cap in captions:
            # Check if caption is on same page
            if cap.page != fig.page:
                continue

            # Calculate vertical distance
            if cap.bbox.bottom <= fig.bbox.top:
                # Caption above figure
                distance = fig.bbox.top - cap.bbox.bottom
            elif cap.bbox.top >= fig.bbox.bottom:
                # Caption below figure
                distance = cap.bbox.top - fig.bbox.bottom
            else:
                continue  # Overlapping, skip

            if distance < min_distance:
                min_distance = distance
                best_caption = cap

        associations.append((fig, best_caption))

    return associations
```

#### Reference Resolution

Linking in-text references ("See Figure 1") to actual figures:

```python
import re

FIGURE_REF_PATTERN = r"(?:Fig(?:ure)?\.?\s*|see\s+)(\d+(?:\.\d+)?)"

def extract_figure_references(text: str) -> list[str]:
    """Extract figure references from text."""
    return re.findall(FIGURE_REF_PATTERN, text, re.IGNORECASE)
```

### 3.3 Vision-Based Approaches

#### ColPali for Figure Retrieval

ColPali embeds document pages as images, enabling direct figure retrieval without extraction:

```python
from byaldi import RAGMultiModalModel

# Index document pages as images
model = RAGMultiModalModel.from_pretrained("vidore/colpali")
model.index(
    input_path="document.pdf",
    index_name="my_index",
    store_collection_with_index=True
)

# Search for figures
results = model.search("chart showing revenue growth", k=5)
# Returns relevant page images containing matching figures
```

**Source:** [Byaldi GitHub](https://github.com/AnswerDotAI/byaldi)

#### VLM Caption Generation

Generate captions for extracted figures using vision models:

```python
import ollama

def generate_caption(image_path: str) -> str:
    """Generate caption using local LLaVA model."""
    response = ollama.chat(
        model="llava:7b",
        messages=[{
            "role": "user",
            "content": "Describe this figure in one sentence for a research paper caption.",
            "images": [image_path]
        }]
    )
    return response["message"]["content"]
```

### 3.4 Current ragd Implementation

**File:** `src/ragd/vision/image.py`

```python
@dataclass
class ExtractedImage:
    """Image extracted from document."""
    image_bytes: bytes
    format: str
    width: int
    height: int
    page_number: int | None
    caption: str = ""  # Optional caption field

def extract_images_from_pdf(
    pdf_path: Path,
    min_width: int = 100,
    min_height: int = 100
) -> list[ExtractedImage]:
    """Extract images using PyMuPDF."""
    ...
```

**Capabilities:**
- ✅ PyMuPDF image extraction
- ✅ Size filtering
- ✅ Optional LLaVA caption generation
- ⚠️ Page number tracking
- ❌ Figure-caption linking
- ❌ Reference resolution

---

## 4. HTML Table Extraction

### 4.1 Static Tables

#### Pandas read_html() (Simplest)

```python
import pandas as pd

# One-liner table extraction
tables = pd.read_html("https://example.com/page.html")

# Returns list of DataFrames, one per table
for i, table in enumerate(tables):
    print(f"Table {i}: {table.shape[0]} rows, {table.shape[1]} cols")
```

**Pros:** Extremely simple, handles most standard tables
**Cons:** No control over parsing, requires lxml/html5lib

#### BeautifulSoup (Flexible)

```python
from bs4 import BeautifulSoup

def extract_tables_bs4(html: str) -> list[dict]:
    """Extract tables with structure preservation."""
    soup = BeautifulSoup(html, "html.parser")
    tables = []

    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                cells.append({
                    "text": cell.get_text(strip=True),
                    "is_header": cell.name == "th",
                    "rowspan": int(cell.get("rowspan", 1)),
                    "colspan": int(cell.get("colspan", 1))
                })
            rows.append(cells)
        tables.append({"rows": rows})

    return tables
```

#### selectolax (10-100x Faster)

```python
from selectolax.parser import HTMLParser

def extract_tables_selectolax(html: str) -> list[str]:
    """Fast table extraction to Markdown."""
    tree = HTMLParser(html)
    tables = []

    for table in tree.css("table"):
        markdown = convert_table_to_markdown(table)
        tables.append(markdown)

    return tables
```

**Performance comparison:**

| Library | 10KB HTML | 100KB HTML | 1MB HTML |
|---------|-----------|------------|----------|
| selectolax | 0.1ms | 0.8ms | 5ms |
| BeautifulSoup (lxml) | 2ms | 15ms | 120ms |
| BeautifulSoup (html.parser) | 5ms | 40ms | 350ms |

### 4.2 Dynamic/JavaScript Tables

For tables rendered via JavaScript:

```python
from playwright.sync_api import sync_playwright

def extract_dynamic_tables(url: str) -> list[str]:
    """Extract tables from JavaScript-rendered pages."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        # Wait for tables to render
        page.wait_for_selector("table")

        # Get rendered HTML
        html = page.content()
        browser.close()

    # Now parse static HTML
    return extract_tables_selectolax(html)
```

### 4.3 Semantic Preservation

#### Handling rowspan/colspan

```python
def normalise_table(rows: list[list[dict]]) -> list[list[str]]:
    """Expand spanning cells into normalised grid."""
    # Determine grid dimensions
    max_cols = max(
        sum(cell["colspan"] for cell in row)
        for row in rows
    )

    grid = [[None] * max_cols for _ in range(len(rows))]

    for row_idx, row in enumerate(rows):
        col_idx = 0
        for cell in row:
            # Find next empty cell
            while col_idx < max_cols and grid[row_idx][col_idx] is not None:
                col_idx += 1

            # Fill spanning cells
            for r in range(cell["rowspan"]):
                for c in range(cell["colspan"]):
                    if row_idx + r < len(grid) and col_idx + c < max_cols:
                        grid[row_idx + r][col_idx + c] = cell["text"]

            col_idx += cell["colspan"]

    return grid
```

#### Markdown Output

```python
def table_to_markdown(grid: list[list[str]], has_header: bool = True) -> str:
    """Convert normalised grid to Markdown table."""
    if not grid:
        return ""

    lines = []
    for i, row in enumerate(grid):
        line = "| " + " | ".join(cell or "" for cell in row) + " |"
        lines.append(line)

        if i == 0 and has_header:
            separator = "| " + " | ".join("---" for _ in row) + " |"
            lines.append(separator)

    return "\n".join(lines)
```

### 4.4 Current ragd Implementation

**File:** `src/ragd/web/structure.py`

```python
@dataclass
class TableInfo:
    markdown: str
    rows: int = 0
    cols: int = 0
    has_header: bool = True

def extract_structure(html: str) -> StructuredContent:
    """Extract tables and structure from HTML."""
    # Uses selectolax (fast) with BeautifulSoup fallback
    ...
```

**Capabilities:**
- ✅ selectolax for performance
- ✅ BeautifulSoup fallback
- ✅ Markdown output
- ✅ Header detection
- ⚠️ Spanning cell handling
- ❌ Table caption extraction

---

## 5. HTML Figure Extraction

### 5.1 `<figure>` and `<figcaption>` Elements

HTML5 provides semantic elements for figures:

```html
<figure>
  <img src="chart.png" alt="Revenue growth chart">
  <figcaption>Figure 1: Q3 2024 revenue growth by region</figcaption>
</figure>
```

**Extraction pattern:**

```python
from selectolax.parser import HTMLParser

@dataclass
class HTMLFigure:
    image_src: str
    alt_text: str
    caption: str
    figure_id: str | None

def extract_figures(html: str) -> list[HTMLFigure]:
    """Extract HTML5 figure elements."""
    tree = HTMLParser(html)
    figures = []

    for figure in tree.css("figure"):
        img = figure.css_first("img")
        figcaption = figure.css_first("figcaption")

        if img:
            figures.append(HTMLFigure(
                image_src=img.attributes.get("src", ""),
                alt_text=img.attributes.get("alt", ""),
                caption=figcaption.text() if figcaption else "",
                figure_id=figure.attributes.get("id")
            ))

    return figures
```

### 5.2 Base64 Image Handling

SingleFile archives embed images as data URIs:

```python
import base64
import re
from io import BytesIO

DATA_URI_PATTERN = r"data:image/(\w+);base64,([A-Za-z0-9+/=]+)"

def extract_data_uri_images(html: str) -> list[tuple[str, bytes]]:
    """Extract Base64-encoded images from HTML."""
    images = []

    for match in re.finditer(DATA_URI_PATTERN, html):
        format_type = match.group(1)  # png, jpeg, etc.
        b64_data = match.group(2)

        try:
            image_bytes = base64.b64decode(b64_data)
            images.append((format_type, image_bytes))
        except Exception:
            continue

    return images
```

### 5.3 Current ragd Gap

**Not implemented:** ragd currently extracts text and tables from HTML but does not extract figures or images.

**Recommendation:** Add `HTMLFigureExtractor` similar to `TableInfo` extraction.

---

## 6. Web Archive Formats

### 6.1 SingleFile HTML

[SingleFile](https://github.com/nickreale/SingleFile) creates self-contained HTML archives with embedded resources.

**Characteristics:**
- All images as Base64 data URIs
- CSS inlined
- JavaScript preserved (optional)
- Single `.html` file

**Extraction approach:**

```python
def process_singlefile(html_path: Path) -> ExtractedContent:
    """Process SingleFile HTML archive."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract text (same as regular HTML)
    text = extract_text_trafilatura(html)

    # Extract tables (same as regular HTML)
    tables = extract_tables(html)

    # Extract embedded images (SingleFile-specific)
    images = extract_data_uri_images(html)

    return ExtractedContent(text=text, tables=tables, images=images)
```

### 6.2 MHTML

MHTML (MIME HTML) uses multipart MIME encoding:

```
MIME-Version: 1.0
Content-Type: multipart/related; boundary="----=_NextPart_..."

------=_NextPart_...
Content-Type: text/html
Content-Location: https://example.com/page.html

<!DOCTYPE html>
<html>...</html>

------=_NextPart_...
Content-Type: image/png
Content-Transfer-Encoding: base64
Content-Location: https://example.com/image.png

iVBORw0KGgoAAAANSUhEUgAA...
```

**Extraction pattern:**

```python
import email
from email import policy

def parse_mhtml(mhtml_path: Path) -> dict:
    """Parse MHTML archive into components."""
    with open(mhtml_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    parts = {"html": None, "images": []}

    for part in msg.walk():
        content_type = part.get_content_type()

        if content_type == "text/html":
            parts["html"] = part.get_content()
        elif content_type.startswith("image/"):
            parts["images"].append({
                "type": content_type,
                "location": part.get("Content-Location"),
                "data": part.get_payload(decode=True)
            })

    return parts
```

### 6.3 Current ragd Support

ragd processes SingleFile and MHTML as standard HTML via the ingestion pipeline. Images embedded as data URIs are not currently extracted.

---

## 7. EPUB/Ebook Extraction

### 7.1 EPUB Structure

EPUB is essentially a ZIP archive containing:

```
my_book.epub/
├── META-INF/
│   └── container.xml      # Points to OPF file
├── OEBPS/
│   ├── content.opf        # Package metadata + manifest
│   ├── toc.ncx            # Navigation (EPUB 2)
│   ├── nav.xhtml          # Navigation (EPUB 3)
│   ├── chapter1.xhtml     # Content files
│   ├── chapter2.xhtml
│   ├── images/
│   │   ├── cover.jpg
│   │   └── figure1.png
│   └── styles/
│       └── style.css
└── mimetype                # "application/epub+zip"
```

### 7.2 Table Extraction from EPUB

EPUB content files are XHTML, so standard HTML parsing applies:

```python
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_tables_from_epub(epub_path: Path) -> list[dict]:
    """Extract all tables from EPUB chapters."""
    book = epub.read_epub(str(epub_path))
    tables = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")

        for table in soup.find_all("table"):
            tables.append({
                "chapter": item.get_name(),
                "markdown": table_to_markdown(table),
                "html": str(table)
            })

    return tables
```

### 7.3 Figure/Image Extraction

```python
def extract_images_from_epub(epub_path: Path) -> list[dict]:
    """Extract all images from EPUB."""
    book = epub.read_epub(str(epub_path))
    images = []

    for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
        images.append({
            "name": item.get_name(),
            "media_type": item.media_type,
            "data": item.get_content()
        })

    # Also check for cover
    cover = None
    for item in book.get_items_of_type(ebooklib.ITEM_COVER):
        cover = item.get_content()

    return images, cover
```

### 7.4 Current ragd Implementation

**File:** `src/ragd/ingestion/office.py`

```python
class EPUBExtractor:
    """Extract text from EPUB ebooks."""

    def extract(self, file_path: Path) -> str:
        book = epub.read_epub(str(file_path))
        texts = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            texts.append(text)

        return "\n\n".join(texts)
```

**Capabilities:**
- ✅ Text extraction from chapters
- ✅ Metadata extraction (title, creator)
- ⚠️ Basic structure (chapter separation)
- ❌ Table extraction
- ❌ Image extraction
- ❌ Figure-caption linking

---

## 8. Caption Extraction Patterns

### 8.1 Caption Detection Regex

```python
# Standard academic caption patterns
CAPTION_PATTERNS = [
    # Figure captions
    r"^Figure\s+(\d+(?:\.\d+)?)[.:\-–]\s*(.+)$",
    r"^Fig\.?\s+(\d+(?:\.\d+)?)[.:\-–]\s*(.+)$",

    # Table captions
    r"^Table\s+(\d+(?:\.\d+)?)[.:\-–]\s*(.+)$",
    r"^Tab\.?\s+(\d+(?:\.\d+)?)[.:\-–]\s*(.+)$",

    # Plate/Chart/Diagram
    r"^(?:Plate|Chart|Diagram|Graph)\s+(\d+(?:\.\d+)?)[.:\-–]\s*(.+)$",

    # Photo credits
    r"^Photo(?:\s+credit)?:\s*(.+)$",
    r"^\((?:Getty|Reuters|AP|AFP|EPA|Shutterstock|iStock|Alamy)[^\)]*\)$",
]

def extract_captions(text: str) -> list[dict]:
    """Extract captions from text."""
    captions = []

    for line in text.split("\n"):
        line = line.strip()
        for pattern in CAPTION_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE | re.MULTILINE)
            if match:
                captions.append({
                    "type": "figure" if "fig" in pattern.lower() else "table",
                    "number": match.group(1) if match.lastindex >= 1 else None,
                    "text": match.group(2) if match.lastindex >= 2 else match.group(1),
                    "raw": line
                })
                break

    return captions
```

### 8.2 Multi-line Caption Handling

Captions often span multiple lines:

```python
def extract_multiline_caption(text: str, start_pattern: str) -> str:
    """Extract caption that may span multiple lines."""
    lines = text.split("\n")
    caption_lines = []
    capturing = False

    for line in lines:
        if re.match(start_pattern, line):
            capturing = True
            caption_lines.append(line)
        elif capturing:
            # Continue capturing if line is indented or doesn't start new element
            if line.startswith(" ") or not re.match(r"^[A-Z]", line):
                caption_lines.append(line.strip())
            else:
                break

    return " ".join(caption_lines)
```

### 8.3 Caption Quality Considerations

**When to preserve captions:**
- Academic documents (essential for understanding)
- Technical manuals (reference material)
- Multi-modal RAG (caption search)

**When to remove captions (F-051 patterns):**
- Web articles with photo credits
- News content with attribution
- Documents where captions add noise

**Current ragd implementation:** `src/ragd/text/captions.py` handles caption removal for text quality.

---

## 9. Best Practices Summary

### By Document Format

| Format | Tables | Figures | Captions | Tool Chain |
|--------|--------|---------|----------|------------|
| **PDF (digital, simple)** | PyMuPDF tables | PyMuPDF images | Heuristic regex | PyMuPDF |
| **PDF (digital, complex)** | Docling TableFormer | Docling layout | Docling caption API | Docling |
| **PDF (scanned)** | Docling + PaddleOCR | OCR + region detection | Spatial proximity | Docling + OCR |
| **PDF (image-heavy)** | VLM direct query | ColPali retrieval | VLM generation | Vision pipeline |
| **HTML** | selectolax | `<figure>` parsing | `<figcaption>` | selectolax/BS4 |
| **SingleFile** | selectolax | Base64 decode | Same as HTML | Custom parser |
| **MHTML** | Parse MIME + selectolax | MIME parts | Same as HTML | email + parser |
| **EPUB** | EbookLib + BS4 | Manifest images | Chapter context | EbookLib |

### Accuracy vs Speed Trade-offs

| Approach | Accuracy | Speed | Use Case |
|----------|----------|-------|----------|
| **VLM direct** | Highest | Slowest | High-value documents |
| **Docling** | 97.9% | Medium | Production PDF processing |
| **PyMuPDF** | 70-80% | Fastest | Simple PDFs, bulk processing |
| **Rule-based** | Variable | Fast | Known formats only |

### Recommended Pipeline

```
Document → Format Detection → Route to Extractor
                                    ↓
         ┌──────────────────────────┼──────────────────────────┐
         ↓                          ↓                          ↓
    [PDF Pipeline]           [HTML Pipeline]            [EPUB Pipeline]
         ↓                          ↓                          ↓
    Quality Check            Parse Structure            Parse Chapters
         ↓                          ↓                          ↓
    Route by Quality         Extract Tables             Extract Tables
    ↓           ↓            Extract Figures            Extract Images
  Simple    Complex                ↓                          ↓
    ↓           ↓            Link Captions              Link Captions
  PyMuPDF   Docling                ↓                          ↓
    ↓           ↓                  ↓                          ↓
    └───────────┴──────────────────┴──────────────────────────┘
                                    ↓
                            Unified Output
                    (Text, Tables, Figures, Captions)
```

---

## 10. Implementation Recommendations for ragd

### Phase 1: HTML Figure Extraction (v0.4+)

**Goal:** Extract `<figure>/<figcaption>` from HTML documents

**Files to modify:**
- `src/ragd/web/structure.py` - Add `FigureInfo` extraction
- `src/ragd/ingestion/extractor.py` - Integrate figure extraction

**Deliverables:**
- `FigureInfo` dataclass with src, alt, caption
- Integration with existing `extract_structure()`

### Phase 2: EPUB Table/Figure Improvements (v0.5+)

**Goal:** Extract tables and images from EPUB chapters

**Files to modify:**
- `src/ragd/ingestion/office.py` - Enhance `EPUBExtractor`

**Deliverables:**
- Table extraction using existing HTML parsing
- Image extraction via EbookLib manifest

### Phase 3: Caption-Element Linking (v0.6+)

**Goal:** Associate extracted captions with their tables/figures

**New module:** `src/ragd/extraction/linker.py`

**Deliverables:**
- Spatial proximity algorithm for PDFs
- DOM-based linking for HTML
- Cross-reference resolution ("See Figure 1")

### Phase 4: Cross-Reference Resolution (v1.0+)

**Goal:** Link in-text references to extracted elements

**Deliverables:**
- Reference pattern detection
- Bidirectional linking (text ↔ figure)
- Search integration

---

## 11. Python Libraries & Dependencies

### Currently Used in ragd

| Library | Purpose | Version |
|---------|---------|---------|
| `docling` | PDF processing, TableFormer | ≥2.0.0 |
| `pymupdf` | PDF parsing, image extraction | ≥1.22.0 |
| `beautifulsoup4` | HTML parsing | ≥4.12.0 |
| `selectolax` | Fast HTML parsing | ≥0.3.0 |
| `ebooklib` | EPUB handling | ≥0.18 |
| `trafilatura` | Web content extraction | ≥1.6.0 |
| `paddleocr` | OCR for scanned docs | ≥2.7.0 |

### Recommended Additions

| Library | Purpose | When to Add |
|---------|---------|-------------|
| `pdffigures2` | Scholarly figure extraction | Phase 3 |
| `grobid-client` | Academic document parsing | Optional |
| `camelot-py` | Alternative table extraction | Evaluation |

### Optional Cloud/API Tools (v2.0+)

| Service | Purpose | Notes |
|---------|---------|-------|
| Claude Vision | VLM table understanding | Best accuracy |
| Unstructured API | Managed extraction | Simplified ops |
| LlamaParse | Cloud PDF parsing | Fast, costly |

---

## 12. References

### Academic Papers

- **Deep Learning for Table Detection Survey (ACM 2024):** [doi.org/10.1145/3657281](https://dl.acm.org/doi/10.1145/3657281)
- **HTTD: Hierarchical Transformer (MDPI 2025):** [mdpi.com/2227-7390/13/2/266](https://www.mdpi.com/2227-7390/13/2/266)
- **Document Parsing Survey (arXiv 2024):** [arxiv.org/abs/2410.21169](https://arxiv.org/abs/2410.21169)
- **PDFFigures 2.0 (JCDL 2016):** [doi.org/10.1145/2910896.2910904](https://dl.acm.org/doi/10.1145/2910896.2910904)

### Benchmarks

- **PDF Extraction Benchmark 2025:** [procycons.com](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/)
- **VLM Document Extraction:** [nanonets.com](https://nanonets.com/blog/vision-language-model-vlm-for-data-extraction/)

### Tools & Libraries

- **Docling:** [github.com/docling-project/docling](https://github.com/docling-project/docling)
- **PDFFigures 2.0:** [github.com/allenai/pdffigures2](https://github.com/allenai/pdffigures2)
- **GROBID:** [github.com/kermitt2/grobid](https://github.com/kermitt2/grobid)
- **EbookLib:** [github.com/aerkalov/ebooklib](https://github.com/aerkalov/ebooklib)
- **Unstructured:** [github.com/Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured)

### ragd Documentation

- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md)
- [State-of-the-Art HTML Processing](./state-of-the-art-html-processing.md)
- [State-of-the-Art Multi-Modal](./state-of-the-art-multi-modal.md)
- [Docling Integration Guide](./docling-integration-guide.md)

---

## Related Documentation

- [F-028: Table Extraction](../features/completed/F-028-table-extraction.md) - TableFormer integration
- [F-019: Multi-Modal Support](../features/completed/F-019-multi-modal-support.md) - Image extraction
- [F-039: Advanced HTML Processing](../features/completed/F-039-advanced-html-processing.md) - trafilatura
- [F-051: Text Quality v2](../features/completed/F-051-text-quality-v2.md) - Caption patterns
- [F-099: PDF Layout Intelligence](../features/completed/F-099-pdf-layout-intelligence.md) - Layout analysis

---

**Status**: Research complete
