# UC-004: Process Messy PDFs

## Summary

User indexes PDFs with complex layouts, scanned pages, or poor quality text extraction.

## User Story

As an end user, I want to index PDFs that have complex layouts, tables, scanned images, or poor OCR quality, so that I can search content from real-world documents that other tools struggle with.

Example of a 'messy' PDFs: A scan of an old book, either as a single PDF file or as a collection of PDFs in a single directory. Pages may or may not be in order (e.g., page x, xi, 1, 2, 3). Some pages may have page numbers while others don't. Some scanned pages may be upside down or roated by 90 degrees.

## Trigger

CLI command: `ragd index <path>` (automatic detection of PDF quality)

## Priority

P0 (Killer Feature)

## Milestone

v0.2

## Preconditions

- ragd is installed and configured
- PDF file exists at specified path
- Docling and OCR dependencies installed (via optional extras)

## Success Criteria

- [ ] Automatic PDF quality assessment (clean vs messy)
- [ ] Clean PDFs processed with standard pipeline (fast)
- [ ] Messy PDFs routed to Docling pipeline
- [ ] Scanned PDFs processed with OCR (PaddleOCR/EasyOCR)
- [ ] Tables extracted and searchable
- [ ] Figures/diagrams preserved with context
- [ ] Processing feedback shows quality detection results
- [ ] Fallback to basic extraction if advanced processing fails
- [ ] User can force specific pipeline via flag

## Derives Features

- [F-009: PDF Quality Detection](../../../development/features/planned/F-009-pdf-quality-detection.md)
- [F-010: Docling Integration](../../../development/features/planned/F-010-docling-integration.md)
- [F-011: OCR Pipeline](../../../development/features/planned/F-011-ocr-pipeline.md)
- [F-012: Table Extraction](../../../development/features/planned/F-012-table-extraction.md)

## Related Use Cases

- [UC-001: Index Documents](./UC-001-index-documents.md)
- [UC-005: Manage Metadata](./UC-005-manage-metadata.md)

## Notes

This is ragd's **killer feature** - the ability to handle messy, real-world PDFs that other RAG tools struggle with. This should be prominently marketed and prioritised for v0.2.

Key differentiators:
- Automatic quality detection (no user configuration needed)
- State-of-the-art document understanding via Docling (IBM)
- Multiple OCR fallbacks for maximum compatibility
- Table and figure preservation

---
