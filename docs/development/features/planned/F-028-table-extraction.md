# F-028: Table Extraction

## Overview

**Use Case**: [UC-004](../../../use-cases/briefs/UC-004-process-messy-pdfs.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Tables are information-dense structures that traditional text extraction destroys. When table cells are extracted as linear text, relationships between rows and columns are lost. This makes tabular data unsearchable and unusable in RAG systems.

## Design Approach

Use Docling's TableFormer model (97.9% cell accuracy) to extract tables as structured data, then convert to searchable formats while preserving structure.

**Table Processing Pipeline:**
```
PDF Page → Layout Analysis
               ↓
         Table Detection
               ↓
         TableFormer Model
               ↓
    Structured Table (rows, cols, cells)
               ↓
    ┌──────────┴──────────┐
    ↓                     ↓
Markdown Table      HTML Table
(for chunks)        (for display)
               ↓
    Table Metadata
    (caption, headers, page)
```

**Output Formats:**

| Format | Use Case |
|--------|----------|
| Markdown | Embedding/chunking (preserves structure in text) |
| HTML | Rich display, complex tables |
| JSON | Programmatic access, downstream processing |

## Implementation Tasks

- [ ] Integrate TableFormer via Docling
- [ ] Implement table to Markdown conversion
- [ ] Implement table to HTML conversion
- [ ] Extract table captions and associate with tables
- [ ] Handle spanning cells (colspan, rowspan)
- [ ] Handle nested tables
- [ ] Create table-specific chunks with context
- [ ] Add table metadata (page, position, caption)

## Success Criteria

- [ ] Tables extracted with >95% cell accuracy
- [ ] Column/row relationships preserved in output
- [ ] Spanning cells handled correctly
- [ ] Table captions associated with table content
- [ ] Tables searchable as part of document content
- [ ] Complex tables (nested, merged cells) handled gracefully

## Dependencies

- [F-026: Docling Integration](./F-026-docling-integration.md) - Provides TableFormer
- [F-003: Chunking Engine](./F-003-chunking-engine.md) - Table-aware chunking

## Technical Notes

**Table to Markdown:**
```python
def table_to_markdown(table):
    """Convert structured table to Markdown format."""
    rows = []

    # Header row
    headers = [cell.text for cell in table.header_cells]
    rows.append("| " + " | ".join(headers) + " |")
    rows.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Data rows
    for row in table.data_rows:
        cells = [cell.text for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)
```

**Table-Aware Chunking:**
- Small tables: Include entire table in single chunk
- Large tables: Chunk by row groups, include header in each chunk
- Always include table caption in chunk context

**Chunk Format Example:**
```markdown
## Table: Quarterly Revenue (from page 15)

| Quarter | Revenue | Growth |
|---------|---------|--------|
| Q1 2024 | $1.2M   | +5%    |
| Q2 2024 | $1.4M   | +17%   |
| Q3 2024 | $1.5M   | +7%    |
```

## Related Documentation

- [State-of-the-Art PDF Processing](../../research/state-of-the-art-pdf-processing.md)
- [LangChain Table RAG Benchmark](https://blog.langchain.com/benchmarking-rag-on-tables/)
- [F-026: Docling Integration](./F-026-docling-integration.md)

---

**Status**: Planned
