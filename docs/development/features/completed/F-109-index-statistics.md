# F-109: Index Statistics

**Status:** Completed
**Milestone:** v0.9.1

## Problem Statement

Users need visibility into their index status beyond basic document counts.

## Design Approach

Provide detailed index statistics via `ragd status --detailed`:
- Document counts by file type
- Chunk statistics
- Storage usage
- Timing information

## Implementation

### Files Created
- `src/ragd/ui/cli/statistics.py` - Statistics module

### Key Components

**IndexStatistics** (dataclass):
- `total_documents` - Total indexed documents
- `total_chunks` - Total chunks
- `documents_by_type` - Breakdown by file extension
- `index_size_bytes` - Storage used
- `last_indexed_at` - Most recent indexing
- Computed properties: `total_size_mb`, `average_chunks_per_doc`

**Functions**:
- `get_index_statistics(data_dir)` - Gather stats from database
- `format_statistics_table(stats, console)` - Rich table output
- `format_statistics_json(stats)` - JSON output
- `format_statistics_plain(stats)` - Plain text output

### CLI Integration

```bash
# Show detailed statistics
ragd status --detailed

# JSON format
ragd status --detailed --format json
```

### Output Example

```
┌─────────────────────────────┐
│      Index Statistics       │
├─────────────────────────────┤
│ Total Documents     1,234   │
│ Total Chunks       45,678   │
│ Avg Chunks/Doc       37.0   │
│ Index Size        123.4 MB  │
│ Last Indexed  2024-12-04    │
└─────────────────────────────┘

Documents by Type
┌──────┬───────┬────────────┐
│ Type │ Count │ Percentage │
├──────┼───────┼────────────┤
│ PDF  │   450 │     36.5%  │
│ TXT  │   320 │     25.9%  │
│ HTML │   200 │     16.2%  │
│ MD   │   264 │     21.4%  │
└──────┴───────┴────────────┘
```

## Implementation Tasks

- [x] Create IndexStatistics dataclass
- [x] Implement database statistics gathering
- [x] Create Rich table formatter
- [x] Create JSON formatter
- [x] Create plain text formatter
- [x] Add tests

## Success Criteria

- [x] Statistics gathered from database
- [x] Multiple output formats supported
- [x] Document type breakdown provided
- [x] Storage usage displayed

## Testing

- 11 tests in `tests/test_statistics.py`
- Tests dataclass properties
- Tests database gathering
- Tests formatters

## Dependencies

- v0.9.0 (Enhanced Indexing)

## Related Documentation

- [F-107: CLI Refinements](./F-107-cli-refinements.md)
- [v0.9.1 Implementation](../../implementation/v0.9.1.md)

