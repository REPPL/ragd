# F-093: Troubleshooting Guide

**Status:** Completed
**Milestone:** v0.8.7

## Problem Statement

Users encounter errors without knowing how to resolve them. A troubleshooting guide reduces support burden.

## Design Approach

Document common issues with symptoms, causes, and solutions.

### Guide Structure
```
docs/guides/troubleshooting.md

## Common Issues
### Installation Issues
### Indexing Issues
### Search Issues
### Performance Issues
### Error Messages
```

### Entry Format
Each issue includes:
1. **Symptom** - What you see
2. **Cause** - Why it happens
3. **Solution** - How to fix it
4. **Prevention** - How to avoid it

### Example
```markdown
### "No documents found" when searching

**Symptom:** Search returns empty results

**Cause:**
- No documents indexed
- Query doesn't match content
- Min score too high

**Solution:**
1. Check indexed documents: `ragd status`
2. Try broader query terms
3. Lower min_score: `ragd search "query" --min-score 0.1`

**Prevention:** Index documents before searching
```

## Implementation Tasks

- [ ] Create docs/guides/troubleshooting.md
- [ ] Document installation issues
- [ ] Document indexing issues (permission, format)
- [ ] Document search issues (no results, slow)
- [ ] Document performance issues
- [ ] Create error message lookup table
- [ ] Add `ragd doctor` suggestions
- [ ] Link from error messages to guide

## Success Criteria

- [ ] 10+ common issues documented
- [ ] Error messages link to solutions
- [ ] `ragd doctor` references guide

## Dependencies

- v0.8.6 (Security Focus)

