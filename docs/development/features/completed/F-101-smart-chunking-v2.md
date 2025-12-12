# F-101: Smart Chunking v2

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Current chunking strategies don't consider content structure. Chunks may split in awkward places, losing semantic coherence.

## Design Approach

Content-aware chunking that respects document structure and semantic boundaries.

### Strategies
- **structural** - Respect headers, paragraphs, lists, code blocks

### Configuration
```yaml
chunking:
  strategy: structural
  respect_headers: true
  respect_lists: true
  respect_code: true
  max_chunk_size: 512
  min_chunk_size: 100
  overlap: 50
```

## Implementation

### Files Created
- `src/ragd/ingestion/smart_chunking.py` - Structural chunking module

### Key Components

**Chunk Dataclass** (lines 13-20):
- `text` - The chunk content
- `start_pos`, `end_pos` - Position in original text
- `chunk_type` - Element type (text, header, list, code)

**StructuralChunker Class** (lines 23-251):
- Configurable chunk size limits
- Header detection via regex (`^#{1,6}\s+`)
- List detection for bullet points
- Code block detection (fenced code blocks)
- Element grouping respects size limits

**Key Methods**:
- `chunk(text)` - Main entry point, returns list of Chunk objects
- `_identify_elements(text)` - Finds structural elements
- `_split_text(text, offset)` - Splits non-code text into elements
- `_group_elements(elements)` - Combines small elements into chunks
- `_estimate_tokens(text)` - Word count * 1.3 approximation

**Convenience Function** (lines 254-282):
- `structural_chunk(text, max_size, overlap, respect_structure)` - Simple interface returning list of strings

## Implementation Tasks

- [x] Implement structural chunker
- [x] Add header/section detection
- [x] Add list preservation
- [x] Add code block preservation
- [x] Add configuration options
- [x] Token estimation

## Success Criteria

- [x] Headers kept with their content
- [x] Lists not split mid-item
- [x] Code blocks preserved intact
- [x] Configurable chunk sizes

## Testing

- 8 tests in `tests/test_ingestion_enhanced.py`
- Tests simple text, headers, code blocks, lists, metadata, token estimation
- All tests passing

## Dependencies

- v0.8.7 (CLI Polish)

## Related Documentation

- [F-003: Chunking Engine](./F-003-chunking-engine.md)
- [v0.9.0 Implementation](../../implementation/v0.9.0.md)

