# Processing Difficult PDFs

Learn to index scanned documents, complex layouts, and tables.

**Time:** 20 minutes
**Prerequisites:** ragd with PDF extras installed, sample PDFs ready
**Validates:** UC-004, F-025, F-026, F-027, F-028

> **Note:** This tutorial is a DRAFT for v0.2 specification validation. Implementation may differ.

---

## What You'll Learn

By the end of this tutorial, you'll know how to:
1. Check PDF processing capabilities
2. Understand quality detection and routing
3. Index scanned documents with OCR
4. Extract tables as searchable content
5. Handle multi-column layouts

---

## Before You Start

### Install PDF Processing Dependencies

ragd's advanced PDF features require optional dependencies:

```bash
# Install PDF processing extras
pip install "ragd[pdf,ocr]"

# Download spaCy model (for metadata extraction)
python -m spacy download en_core_web_sm
```

### Verify Installation

Check that PDF processing is available:

```bash
ragd doctor
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ragd Health Check                        │
├─────────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Healthy                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✅ Storage          ChromaDB accessible                     │
│ ✅ Embedding        Model loaded successfully               │
│ ✅ Configuration    Valid configuration                     │
│ ✅ Dependencies     All packages installed                  │
│ ✅ PDF Processing   Docling available                       │
│ ✅ OCR              PaddleOCR available                     │
└─────────────────────────────────────────────────────────────┘
```

### Prepare Sample Documents

For this tutorial, you'll need different types of PDFs:

1. **Simple PDF** - A digital-native PDF with text (any research paper)
2. **Scanned PDF** - A scan of a printed document
3. **PDF with tables** - A document containing data tables
4. **Multi-column PDF** - A two-column academic paper

Don't have these? Download samples:

```bash
# Create a samples directory
mkdir -p ~/ragd-samples

# Download a simple research paper
curl -o ~/ragd-samples/simple.pdf "https://arxiv.org/pdf/2408.09869"

# For scanned documents, scan any printed page or use a test scan
```

---

## Step 1: Check PDF Quality

Before indexing, understand what type of PDF you're working with:

```bash
ragd inspect ~/ragd-samples/simple.pdf
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│                    PDF Analysis                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ File: simple.pdf                                            │
│ Pages: 12                                                   │
│                                                             │
│ Quality Assessment:                                         │
│ ┌─────────────────────┬─────────────────────────┐          │
│ │ Text Layer          │ ✅ Present (98% coverage)│         │
│ │ Image Density       │ Low (3 figures)          │         │
│ │ Layout Complexity   │ Single-column            │         │
│ │ Tables Detected     │ 2 tables                 │         │
│ │ Scan Probability    │ 2% (digital-native)      │         │
│ └─────────────────────┴─────────────────────────┘          │
│                                                             │
│ Recommended Pipeline: fast (PyMuPDF)                        │
│ Estimated Processing Time: <5 seconds                       │
└─────────────────────────────────────────────────────────────┘
```

**What the quality assessment tells you:**
- **Text Layer**: Whether the PDF has extractable text
- **Scan Probability**: How likely the document is a scan
- **Recommended Pipeline**: Which processing path ragd will use

**Checkpoint:** Quality assessment completes successfully

---

## Step 2: Index a Simple PDF

For digital-native PDFs with good text layers, ragd uses the fast path:

```bash
ragd index ~/ragd-samples/simple.pdf
```

**Expected output:**
```
Indexing: simple.pdf
  ├─ Analysing quality... digital-native
  ├─ Pipeline: fast (PyMuPDF)
  ├─ Extracting text... done (0.3s)
  ├─ Creating chunks... 45 chunks
  ├─ Generating embeddings... done
  └─ Storing in database... done

✅ Indexed 1 document (45 chunks)
   Processing time: 2.1 seconds
```

**Why this is fast:** Digital-native PDFs have embedded text that can be extracted directly without OCR.

**Checkpoint:** Simple PDF indexed in under 5 seconds

---

## Step 3: Index a Scanned Document

Scanned documents require OCR. Let's process one:

```bash
ragd index ~/ragd-samples/scanned.pdf
```

**Expected output:**
```
Indexing: scanned.pdf
  ├─ Analysing quality... scanned document detected
  ├─ Pipeline: ocr (PaddleOCR)
  ├─ Converting pages to images... 5 pages
  ├─ Running OCR...
  │   Page 1/5 (confidence: 0.94)
  │   Page 2/5 (confidence: 0.91)
  │   Page 3/5 (confidence: 0.89)
  │   Page 4/5 (confidence: 0.92)
  │   Page 5/5 (confidence: 0.88)
  ├─ Average confidence: 0.91 (good)
  ├─ Creating chunks... 28 chunks
  ├─ Generating embeddings... done
  └─ Storing in database... done

✅ Indexed 1 document (28 chunks)
   Processing time: 45.2 seconds
   OCR confidence: 91%
```

**Understanding OCR confidence:**
- **90-100%**: Excellent - results highly reliable
- **70-89%**: Good - most text correct, some errors possible
- **50-69%**: Fair - review results, consider rescanning
- **Below 50%**: Poor - significant errors likely

**Checkpoint:** Scanned PDF indexed with OCR confidence reported

---

## Step 4: Handle Low-Confidence OCR

If OCR confidence is low, ragd warns you:

```bash
ragd index ~/ragd-samples/poor-quality-scan.pdf
```

**Expected output (low confidence):**
```
Indexing: poor-quality-scan.pdf
  ├─ Analysing quality... scanned document detected
  ├─ Pipeline: ocr (PaddleOCR)
  ├─ Running OCR...
  │   Page 1/3 (confidence: 0.52)
  │   Page 2/3 (confidence: 0.48)
  │   Page 3/3 (confidence: 0.55)
  ├─ Average confidence: 0.52 (fair)
  │
  │ ⚠️  Low OCR confidence detected
  │    Results may contain errors.
  │    Consider:
  │    - Rescanning at higher resolution
  │    - Using --force-accurate for better OCR
  │    - Reviewing extracted text with 'ragd show'
  │
  ├─ Creating chunks... 15 chunks
  └─ Storing in database... done

⚠️  Indexed 1 document with warnings
    OCR confidence: 52% (fair)
```

**Options for low-confidence documents:**

```bash
# Force more accurate (but slower) OCR
ragd index poor-quality-scan.pdf --force-accurate

# Skip low-confidence documents
ragd index ~/scans/ --min-confidence 0.7
```

**Checkpoint:** Understand how to handle low-confidence OCR

---

## Step 5: Extract Tables

PDFs with tables get special processing to preserve structure:

```bash
ragd index ~/ragd-samples/report-with-tables.pdf
```

**Expected output:**
```
Indexing: report-with-tables.pdf
  ├─ Analysing quality... digital-native
  ├─ Pipeline: structure (Docling)
  ├─ Extracting content...
  │   Text blocks: 23
  │   Tables: 4 (extracting structure...)
  │   Figures: 2
  ├─ Table extraction:
  │   Table 1: 5x3 (extracted as Markdown)
  │   Table 2: 12x6 (extracted as Markdown)
  │   Table 3: 8x4 (extracted as Markdown)
  │   Table 4: 3x2 (extracted as Markdown)
  ├─ Creating chunks... 52 chunks (including table content)
  └─ Storing in database... done

✅ Indexed 1 document (52 chunks)
   Tables extracted: 4
```

**Searching tables:**

```bash
ragd search "quarterly revenue figures"
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search Results for: "quarterly revenue figures"          │
├─────────────────────────────────────────────────────────────┤
│ 1. report-with-tables.pdf (Score: 0.87)                     │
│    Table 2, Page 5                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ | Quarter | Revenue | Growth |                          │ │
│ │ |---------|---------|--------|                          │ │
│ │ | Q1 2024 | $2.3M   | +12%   |                          │ │
│ │ | Q2 2024 | $2.8M   | +22%   |                          │ │
│ │ | Q3 2024 | $3.1M   | +11%   |                          │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Tables searchable as structured content

---

## Step 6: Process Multi-Column Layouts

Two-column academic papers need special handling to maintain reading order:

```bash
ragd index ~/ragd-samples/two-column-paper.pdf
```

**Expected output:**
```
Indexing: two-column-paper.pdf
  ├─ Analysing quality... digital-native, complex layout
  ├─ Pipeline: structure (Docling)
  ├─ Layout analysis:
  │   Layout type: two-column
  │   Reading order: detected
  │   Sections: 8
  ├─ Extracting in reading order... done
  ├─ Creating chunks... 67 chunks
  └─ Storing in database... done

✅ Indexed 1 document (67 chunks)
   Layout: two-column (reading order preserved)
```

**Why reading order matters:**
Without layout analysis, text from two columns might be interleaved incorrectly. Docling detects the layout and extracts text in the correct reading order.

**Checkpoint:** Multi-column PDF indexed with correct reading order

---

## Step 7: Batch Process a Directory

Index multiple PDFs at once:

```bash
ragd index ~/ragd-samples/ --recursive
```

**Expected output:**
```
Scanning: ~/ragd-samples/
Found 5 PDF files

Processing:
  1/5 simple.pdf ...................... ✅ fast (2.1s)
  2/5 scanned.pdf ..................... ✅ ocr (45.2s)
  3/5 report-with-tables.pdf .......... ✅ structure (8.3s)
  4/5 two-column-paper.pdf ............ ✅ structure (6.7s)
  5/5 poor-quality-scan.pdf ........... ⚠️ ocr (32.1s, 52% confidence)

┌─────────────────────────────────────────────────────────────┐
│                    Indexing Summary                         │
├─────────────────────────────────────────────────────────────┤
│ Documents processed: 5                                      │
│ Total chunks: 207                                           │
│ Processing time: 1m 34s                                     │
│                                                             │
│ By pipeline:                                                │
│   fast: 1 document                                          │
│   structure: 2 documents                                    │
│   ocr: 2 documents                                          │
│                                                             │
│ ⚠️  1 document with low OCR confidence                      │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Batch processing completes with summary

---

## Step 8: View Extracted Content

Verify what was extracted from a document:

```bash
ragd show ~/ragd-samples/report-with-tables.pdf
```

**Expected output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Document: report-with-tables.pdf                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Metadata:                                                   │
│   Title: Q3 2024 Financial Report                           │
│   Author: Finance Team                                      │
│   Pages: 12                                                 │
│   Indexed: 2025-11-26 14:32:15                              │
│   Pipeline: structure (Docling)                             │
│                                                             │
│ Content Statistics:                                         │
│   Chunks: 52                                                │
│   Tables: 4                                                 │
│   Figures: 2                                                │
│                                                             │
│ Extracted Tables:                                           │
│   [1] Revenue by Quarter (5x3) - Page 3                     │
│   [2] Quarterly Revenue (12x6) - Page 5                     │
│   [3] Cost Breakdown (8x4) - Page 7                         │
│   [4] Summary (3x2) - Page 11                               │
│                                                             │
│ View full content: ragd show report.pdf --content           │
│ View specific table: ragd show report.pdf --table 2         │
└─────────────────────────────────────────────────────────────┘
```

**Checkpoint:** Can view document metadata and structure

---

## What You Learned

Congratulations! You've completed the difficult PDFs tutorial. You now know how to:

| Task | Command |
|------|---------|
| Check PDF quality | `ragd inspect <file>` |
| Index with OCR | `ragd index <scanned.pdf>` |
| Force accurate OCR | `ragd index <file> --force-accurate` |
| Set confidence threshold | `ragd index <dir> --min-confidence 0.7` |
| View extracted content | `ragd show <file>` |
| View specific table | `ragd show <file> --table <n>` |

---

## Pipeline Selection Summary

| Document Type | Pipeline | Speed | When Used |
|---------------|----------|-------|-----------|
| Digital with text | fast (PyMuPDF) | ~0.5s/page | Text layer present, simple layout |
| Complex layout | structure (Docling) | ~2s/page | Tables, multi-column, figures |
| Scanned | ocr (PaddleOCR) | ~10s/page | No text layer, scan detected |

---

## Next Steps

- **Organise with metadata:** [Organising Your Knowledge Base](./organising-knowledge-base.md)
- **Back up your data:** [Backing Up Your Data](./backing-up-data.md)
- **Configure OCR:** [OCR Configuration Guide](../guides/ocr-configuration.md)

---

## Troubleshooting

### "Docling not available"

Install PDF processing dependencies:
```bash
pip install "ragd[pdf]"
```

### "OCR engine not found"

Install OCR dependencies:
```bash
pip install "ragd[ocr]"
```

### OCR is very slow

- First run downloads models (~150MB)
- Subsequent runs are faster
- Use `--force-fast` to skip OCR for digital PDFs
- Consider using `--max-pages` for large documents

### "Table extraction failed"

- Very complex tables may not extract perfectly
- Check with `ragd show <file> --table <n>`
- Report issues with sample documents

### Low OCR confidence

- Check scan quality (300 DPI recommended)
- Ensure good lighting, no skew
- Try `--force-accurate` for better results
- Consider rescanning problematic documents

---

## Related Documentation

- [UC-004: Process Messy PDFs](../use-cases/briefs/UC-004-process-messy-pdfs.md)
- [F-025: PDF Quality Detection](../development/features/planned/F-025-pdf-quality-detection.md)
- [F-026: Docling Integration](../development/features/planned/F-026-docling-integration.md)
- [F-027: OCR Pipeline](../development/features/planned/F-027-ocr-pipeline.md)
- [F-028: Table Extraction](../development/features/planned/F-028-table-extraction.md)
- [ADR-0019: PDF Processing](../development/decisions/adrs/0019-pdf-processing.md)

---
