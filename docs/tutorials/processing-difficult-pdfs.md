# Processing Difficult PDFs

Learn how to handle scanned documents, OCR, and complex PDF layouts with ragd.

**Time:** 20 minutes
**Level:** Intermediate
**Prerequisites:** Completed Getting Started tutorial, documents to test with

## What You'll Learn

- Understanding PDF quality detection
- Configuring OCR for scanned documents
- Handling multi-column layouts
- Assessing extraction quality
- Troubleshooting poor extractions

## Understanding PDF Types

ragd automatically detects PDF quality and routes documents through the appropriate pipeline:

| PDF Type | Detection | Processing Path |
|----------|-----------|-----------------|
| **Native text** | Has extractable text layer | Fast path (PyMuPDF) |
| **Scanned** | No text, uniform resolution | OCR path (Docling + PaddleOCR) |
| **Complex layout** | Tables, multi-column | Structure path (Docling) |

You don't need to manually specify which path to use—ragd handles this automatically.

## Step 1: Index Your PDFs

Index PDFs normally:

```bash
ragd index ~/Documents/scanned-papers/
```

ragd will:
1. Analyse each PDF to determine quality
2. Route to the appropriate extraction pipeline
3. Apply OCR where needed
4. Report any quality concerns

## Step 2: Check Extraction Quality

After indexing, review the quality of extracted content:

```bash
# Summary of all documents
ragd quality

# Detailed view of a specific document
ragd quality doc-123 --verbose

# Find documents with quality issues
ragd quality --below 0.7

# Check only PDFs
ragd quality --type pdf
```

### Quality Metrics

| Metric | Description | Good Score |
|--------|-------------|------------|
| Completeness | Text coverage vs source | > 0.8 |
| Character quality | Recognition accuracy | > 0.9 |
| Structure | Headers/lists preserved | > 0.7 |
| Overall | Combined score | > 0.75 |

## Step 3: Install OCR Dependencies (If Needed)

For scanned documents, install OCR support:

```bash
# PaddleOCR (recommended - best accuracy)
pip install paddlepaddle paddleocr

# Or EasyOCR (alternative)
pip install easyocr
```

After installing, re-index scanned documents:

```bash
ragd reindex --type pdf
```

## Step 4: Configure OCR Settings

Edit `~/.ragd/config.yaml` to tune OCR behaviour:

```yaml
pdf:
  # Quality routing thresholds
  quality_threshold: 0.8    # Below this triggers structure path
  ocr_threshold: 0.3        # Below this triggers OCR path

  # OCR settings
  ocr:
    engine: paddleocr       # paddleocr | easyocr | tesseract
    confidence_threshold: 0.7
    language: en            # Language code
    dpi: 300                # Higher = better quality, slower

  # Layout analysis
  layout_analysis: true
  extract_tables: true
```

## Step 5: Handle Specific Issues

### Low OCR Confidence

If you see warnings about low OCR confidence:

```bash
# Check specific document
ragd quality doc-123 --verbose
```

Options:
1. **Higher DPI** - Increase `dpi` setting in config
2. **Different engine** - Try `easyocr` if `paddleocr` struggles
3. **Manual review** - Some documents may need manual transcription

### Multi-Column Documents

ragd's Docling integration handles multi-column layouts automatically. If columns are mixed up:

```yaml
pdf:
  layout_analysis: true
  preserve_reading_order: true
```

### Tables Not Extracted

Enable table extraction:

```yaml
pdf:
  extract_tables: true
  table_format: markdown    # markdown | csv | plain
```

## Step 6: Re-index Problem Documents

After adjusting settings, re-index specific documents:

```bash
# Re-index a specific document
ragd reindex doc-123

# Re-index all PDFs
ragd reindex --type pdf

# Re-index everything (with confirmation)
ragd reindex --all
```

## Verification

You've succeeded if:
- [ ] `ragd quality` shows quality scores for your PDFs
- [ ] Scanned documents have searchable text
- [ ] Quality scores are above 0.7 for most documents
- [ ] Multi-column documents read in correct order

## Example Workflow

```bash
# 1. Index a collection of PDFs
ragd index ~/Papers/

# 2. Check overall quality
ragd quality --type pdf

# 3. Identify problem documents
ragd quality --below 0.6 --type pdf

# 4. Check specific document details
ragd quality doc-456 --verbose

# 5. After config changes, re-index low-quality docs
ragd reindex doc-456

# 6. Verify improvement
ragd quality doc-456
```

## Next Steps

- [Organising Your Knowledge Base](organising-knowledge-base.md) - Tag and organise documents
- [Powerful Searching](powerful-searching.md) - Search your indexed PDFs

---

## Troubleshooting

**"OCR not available"**
- Install PaddleOCR: `pip install paddlepaddle paddleocr`
- Or install EasyOCR: `pip install easyocr`

**Very slow indexing**
- First OCR run downloads models (one-time)
- Reduce DPI for faster processing: `dpi: 150`
- Process fewer pages at once

**Garbled text output**
- Document may be a scan - check with `ragd quality doc-123`
- Ensure OCR is installed
- Try a different OCR engine

**Tables appear as plain text**
- Enable `extract_tables: true` in config
- Re-index the document

---

## Related Documentation

- [Tutorial: Getting Started](01-getting-started.md)
- [Guide: Advanced Indexing](../guides/indexing-advanced.md)
- [F-027: OCR Pipeline](../development/features/completed/F-027-ocr-pipeline.md)
