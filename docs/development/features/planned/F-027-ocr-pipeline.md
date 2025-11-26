# F-027: OCR Pipeline

## Overview

**Use Case**: [UC-004](../../../use-cases/briefs/UC-004-process-messy-pdfs.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Scanned documents have no extractable text layer—they are images of text. Without OCR (Optical Character Recognition), these documents cannot be indexed or searched. However, OCR introduces errors that cascade through RAG systems, reducing retrieval accuracy by up to 50% (OHRBench findings).

## Design Approach

Implement a multi-tier OCR pipeline that balances accuracy with performance, using Docling's OCR integration as primary and standalone OCR engines as fallback.

**OCR Strategy:**
```
Scanned PDF → Docling + OCR Backend
                    ↓
              ┌─────┴─────┐
              ↓           ↓
         PaddleOCR    EasyOCR
        (Primary)    (Fallback)
              ↓
    Text + Confidence Scores
              ↓
    Quality Threshold Check
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
  Accept            Low Confidence
                    Warning + Accept
```

**Engine Selection:**

| Engine | Accuracy | Speed | Best For |
|--------|----------|-------|----------|
| PaddleOCR | 93% | Fast | Complex layouts, multi-language |
| EasyOCR | 85% | Medium | Scene text, GPU environments |
| Tesseract | 89% | Slow | Simple layouts, CPU-only |

## Implementation Tasks

- [ ] Add OCR dependencies as optional extras (`pip install ragd[ocr]`)
- [ ] Implement PaddleOCR backend (primary)
- [ ] Implement EasyOCR backend (fallback)
- [ ] Create confidence score aggregation
- [ ] Add low-confidence warnings to output
- [ ] Implement page orientation detection and correction
- [ ] Add language detection for multi-language documents
- [ ] Configure DPI settings for quality vs speed trade-off

## Success Criteria

- [ ] Scanned PDFs produce searchable text
- [ ] Confidence scores reported per page
- [ ] Processing time acceptable (<30s per page)
- [ ] Low-confidence regions flagged in output
- [ ] Rotated pages auto-corrected before OCR
- [ ] Multi-language documents supported

## Dependencies

- [F-025: PDF Quality Detection](./F-025-pdf-quality-detection.md) - Routes to OCR path
- [F-026: Docling Integration](./F-026-docling-integration.md) - Docling orchestrates OCR
- PaddleOCR or EasyOCR library

## Technical Notes

**Installation:**
```bash
# PaddleOCR (recommended)
pip install paddlepaddle paddleocr

# EasyOCR (alternative)
pip install easyocr
```

**Confidence Handling:**
```python
def process_with_ocr(image):
    result = ocr.ocr(image)

    texts = []
    low_confidence_regions = []

    for line in result:
        text, confidence = line[1]
        texts.append(text)

        if confidence < 0.7:
            low_confidence_regions.append({
                "text": text,
                "confidence": confidence,
                "bbox": line[0]
            })

    return {
        "text": "\n".join(texts),
        "avg_confidence": mean([l[1][1] for l in result]),
        "low_confidence_regions": low_confidence_regions
    }
```

**OHRBench Mitigation:**
- Report OCR confidence to users
- Consider post-OCR spell checking for critical documents
- Flag documents with <70% average confidence for manual review

## Related Documentation

- [State-of-the-Art PDF Processing](../../research/state-of-the-art-pdf-processing.md)
- [OHRBench Paper](https://arxiv.org/abs/2412.02592)
- [F-026: Docling Integration](./F-026-docling-integration.md)

---

**Status**: Planned
