# F-001: Document Ingestion Pipeline

## Overview

**Use Case**: [UC-001: Index Documents](../../../use-cases/briefs/UC-001-index-documents.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Users need a reliable way to add documents to their knowledge base. The ingestion pipeline must handle file discovery, format detection, and orchestrate the downstream processing (extraction, chunking, embedding).

## Design Approach

### Architecture

```
User Input (path)
    ↓
File Discovery (glob patterns, recursion)
    ↓
Format Detection (extension, magic bytes)
    ↓
Processing Router
    ↓
[F-002: Text Extraction] → [F-003: Chunking] → [F-004: Embedding] → Storage
```

### Technologies

- **pathlib**: Cross-platform path handling
- **python-magic**: File type detection (optional, fallback to extension)
- **asyncio**: Concurrent file processing for batch operations

### CLI Interface

```bash
# Single file
ragd index document.pdf

# Directory (recursive)
ragd index ./documents/

# With options
ragd index ./documents/ --recursive --format pdf,txt,md
```

## Implementation Tasks

- [ ] Create `FileDiscovery` class for path resolution and globbing
- [ ] Implement format detection with extension and magic byte support
- [ ] Build `IngestionPipeline` orchestrator class
- [ ] Add progress tracking with Rich progress bars
- [ ] Implement duplicate detection (hash-based)
- [ ] Create `ragd index` CLI command
- [ ] Add batch processing with configurable concurrency
- [ ] Write unit tests for file discovery and format detection
- [ ] Write integration tests for full pipeline

## Success Criteria

- [ ] Single file indexing works for PDF, TXT, MD formats
- [ ] Directory indexing with recursive option works
- [ ] Progress feedback shown during processing
- [ ] Duplicate files detected and skipped with message
- [ ] Errors handled gracefully with clear messages
- [ ] Processing completes within reasonable time (< 1s per simple document)

## Dependencies

- Python 3.12
- Rich (progress bars)
- Typer (CLI)
- ChromaDB (storage)

## Technical Notes

### Duplicate Detection

Use SHA-256 hash of file content for duplicate detection. Store hashes in metadata alongside embeddings.

### Error Handling

- Missing files: Clear error message, continue with other files
- Unsupported format: Warning message, skip file
- Extraction failure: Log error, attempt fallback extraction

### Configuration

```yaml
ingestion:
  supported_formats: [pdf, txt, md, html]
  max_file_size_mb: 100
  concurrent_workers: 4
  recursive_default: true
```

## Related Documentation

- [F-002: Text Extraction](./F-002-text-extraction.md) - Downstream dependency
- [F-003: Chunking Engine](./F-003-chunking-engine.md) - Downstream dependency
- [F-004: Embedding Generation](./F-004-embedding-generation.md) - Downstream dependency
- [UC-001: Index Documents](../../../use-cases/briefs/UC-001-index-documents.md) - Parent use case

---
