# F-025: PDF Quality Detection

## Overview

**Use Case**: [UC-004](../../../use-cases/briefs/UC-004-process-messy-pdfs.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Not all PDFs are equal. Digital-native PDFs with embedded text can be processed quickly and accurately with simple extraction. Scanned PDFs, complex layouts, and degraded documents require heavyweight processing (OCR, layout analysis). Without automatic quality detection, users must manually specify which pipeline to use, or the system wastes resources running expensive processing on simple documents.

## Design Approach

Implement a quality detection pipeline that classifies PDFs before routing them through appropriate processing paths:

```
PDF Input → Quality Analysis → Route Decision
                                    ↓
            ┌───────────────────────┼───────────────────────┐
            ↓                       ↓                       ↓
    Fast Path               Structure Path           OCR Path
   (PyMuPDF4LLM)              (Docling)         (Docling + OCR)
```

**Classification Criteria:**

| Factor | Detection Method | Weight |
|--------|------------------|--------|
| Text layer present | PDF text extraction attempt | High |
| Text quality | Character recognition confidence | High |
| Layout complexity | Page element analysis | Medium |
| Image ratio | Image vs text area | Medium |
| Scan indicators | Resolution uniformity, noise patterns | Low |

## Implementation Tasks

- [ ] Create PDF analyser class with quality scoring
- [ ] Implement text layer detection (does extractable text exist?)
- [ ] Implement scan detection (is this a scanned document?)
- [ ] Implement complexity scoring (tables, multi-column, figures)
- [ ] Create routing logic based on quality score
- [ ] Add `--force-pipeline` CLI flag for manual override
- [ ] Add quality report to processing feedback

## Success Criteria

- [ ] Digital-native PDFs correctly classified as "fast path" (>95% accuracy)
- [ ] Scanned PDFs correctly classified as "OCR path" (>90% accuracy)
- [ ] Complex layouts correctly classified as "structure path" (>85% accuracy)
- [ ] Quality analysis completes in <500ms per document
- [ ] User can override classification via CLI flag

## Dependencies

- [F-002: Text Extraction](./F-002-text-extraction.md) - Basic extraction for quality testing
- PyMuPDF for PDF analysis

## Technical Notes

**Quality Score Formula:**
```python
quality_score = (
    text_layer_score * 0.4 +
    text_quality_score * 0.3 +
    complexity_score * 0.2 +
    scan_indicator_score * 0.1
)

# Routing thresholds
if quality_score > 0.8:
    return "fast_path"      # PyMuPDF4LLM
elif is_scanned:
    return "ocr_path"       # Docling + PaddleOCR
else:
    return "structure_path" # Docling
```

**OHRBench Insight:** From research, OCR errors cascade through RAG systems causing up to 50% retrieval degradation. Quality detection enables us to minimise OCR usage when unnecessary.

## Related Documentation

- [State-of-the-Art PDF Processing](../../research/state-of-the-art-pdf-processing.md)
- [F-026: Docling Integration](./F-026-docling-integration.md)
- [F-027: OCR Pipeline](./F-027-ocr-pipeline.md)

