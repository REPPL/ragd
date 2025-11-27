# F-051: Text Quality v2

## Overview

**Use Case**: Improved text extraction quality
**Milestone**: v0.3.0
**Priority**: P1

## Problem Statement

Text extracted from HTML and PDF documents often contains artefacts that degrade search quality:
- HTML line breaks inserted incorrectly (BeautifulSoup `separator="\n"`)
- Site-specific boilerplate (Medium, NYT, LinkedIn navigation)
- Figure captions and photo credits polluting content
- OCR ligature errors (fi/fl confusion)
- Inconsistent whitespace and formatting

These issues reduce retrieval accuracy and create poor user experience when viewing search results.

## Design Approach

Implement a comprehensive text quality pipeline with multiple stages:

1. **Trafilatura-first HTML extraction**: Use trafilatura for article extraction before falling back to BeautifulSoup
2. **Site-specific boilerplate removal**: Pattern matching for common site navigation
3. **Caption and credit removal**: Detect and remove figure captions, photo credits, media attributions
4. **Ligature error correction**: Fix common OCR errors (defi→define, ofice→office)
5. **Line break normalisation**: Fix incorrect line breaks from HTML extraction
6. **Reindex command**: Allow users to re-process existing documents

**Command Interface:**

```bash
ragd reindex --all              # Re-index all documents
ragd reindex --type pdf         # Re-index only PDFs
ragd reindex doc-123            # Re-index specific document
ragd reindex --all --force      # Re-index without confirmation
```

## Implementation Tasks

- [x] Create `ragd.text.captions` module for caption/credit removal
- [x] Add site-specific patterns to `ragd.text.html_clean`
- [x] Add `fix_html_line_breaks()` function
- [x] Add `fix_ligature_errors()` to `ragd.text.pdf_fixes`
- [x] Add `fix_title_ocr()` for title-specific corrections
- [x] Update `normalise()` to accept `source_url` parameter
- [x] Implement trafilatura-first strategy in `HTMLExtractor`
- [x] Use space separator in BeautifulSoup fallback
- [x] Add `ragd reindex` CLI command
- [x] Create unit tests for caption removal

## Success Criteria

- [x] Trafilatura used for HTML extraction when available
- [x] Site-specific boilerplate removed
- [x] Figure captions and photo credits stripped
- [x] OCR ligature errors corrected
- [x] Line breaks normalised correctly
- [x] Reindex command functional
- [x] All existing tests pass

## Dependencies

- [F-039: Advanced HTML Processing](./F-039-advanced-html-processing.md) - trafilatura integration

## Technical Notes

**Caption Patterns:**

```python
CAPTION_PATTERNS = [
    r"^Figure\s+\d+[.:\-]\s*.+$",
    r"^Table\s+\d+[.:\-]\s*.+$",
    r"^Photo(?:\s+credit)?:\s*.+$",
    r"^\((?:Getty\s*Images?|Reuters|AP|AFP|EPA|Shutterstock|iStock|Alamy)\)$",
    # ... more patterns
]
```

**Ligature Corrections:**

```python
LIGATURE_PATTERNS = [
    (r"\bii([aeiou])", r"fi\1"),  # iinal → final
    (r"\bdeii", "defi"),          # deiine → define
    (r"\bofice", "office"),       # ofice → office
]
```

## Related Documentation

- [F-039: Advanced HTML Processing](./F-039-advanced-html-processing.md)
- [v0.3.0 Milestone](../../milestones/v0.3.0.md)

---

**Status**: Completed
