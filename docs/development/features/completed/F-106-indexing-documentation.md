# F-106: Indexing Documentation

**Status:** Completed
**Milestone:** v0.9.1

## Problem Statement

v0.9.0 introduced several new indexing features that need documentation for users.

## Design Approach

Create comprehensive documentation for:
- New file type support (EPUB, DOCX, XLSX)
- Smart chunking configuration
- Indexing resume/checkpoint
- Change detection and duplicate handling

## Implementation

### Files Created
- `docs/guides/indexing-advanced.md` - Advanced indexing guide

### Documentation Sections

1. **New File Types**
   - EPUB extraction with ebooklib
   - DOCX extraction with python-docx
   - XLSX extraction with openpyxl
   - Installation instructions

2. **Smart Chunking**
   - Configuration options
   - Structural chunking explanation
   - Example input/output

3. **Indexing Resume**
   - Checkpoint enabling
   - Resume commands
   - Checkpoint file format

4. **Change Detection**
   - How detection works
   - Force re-indexing option

5. **Duplicate Detection**
   - Policy configuration
   - Available policies (skip, index_all, link)

6. **Best Practices**
   - Large collections guidance
   - Mixed file type handling
   - Performance optimisation

## Implementation Tasks

- [x] Document new file type support
- [x] Document smart chunking configuration
- [x] Document indexing resume feature
- [x] Document change detection
- [x] Document duplicate detection
- [x] Add best practices section

## Success Criteria

- [x] All v0.9.0 features documented
- [x] Clear installation instructions for optional dependencies
- [x] Configuration examples provided
- [x] Best practices included

## Dependencies

- v0.9.0 (Enhanced Indexing)

## Related Documentation

- [Guide: Advanced Indexing](../../../guides/indexing-advanced.md)
- [v0.9.1 Implementation](../../implementation/v0.9.1.md)

