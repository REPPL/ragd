# Devlog: v0.8.1 Intelligent Tagging

**Date:** 2025-12-03
**Version:** 0.8.1
**Theme:** Intelligence & Organisation - Intelligent Tagging

## The Story

Following on from v0.8.0's foundation, v0.8.1 delivers the "intelligent" part of intelligent tagging. Three interconnected features that transform how documents are organised and discovered.

## What We Built

### Smart Collections (F-063)

Think "smart playlists" but for documents. Instead of manually adding files to folders, you define a query and the collection maintains itself.

```bash
# All project docs that aren't archived
ragd collection create "active-projects" \
  --include-any "project/*" \
  --exclude "status/archived"

# See what's in it
ragd collection show "active-projects"
# 47 documents matching query
```

The query engine supports AND/OR/NOT logic with wildcard patterns:
- `include_all` - all tags must be present (AND)
- `include_any` - at least one tag (OR)
- `exclude` - none of these tags (NOT)

Collections can even be nested - a "critical-projects" collection could be a child of "active-projects".

### Auto-Tag Suggestions (F-061)

With v0.8.0's tag provenance in place, we can now track where tags come from. The suggestion engine stores recommendations from various sources:

```python
TagSuggestion.from_keybert(doc_id, "machine-learning", 0.89)
TagSuggestion.from_llm(doc_id, "technical-report", 0.95, model="llama3.2")
TagSuggestion.from_ner(doc_id, "OpenAI", "ORG", 0.92)  # -> org/openai
```

Users can review and confirm/reject suggestions:

```bash
ragd tag pending                    # What's waiting for review?
ragd tag confirm doc-123 --min-confidence 0.85  # Accept the good ones
ragd tag reject doc-123 topic/spam  # Reject the bad
```

### Tag Library Management (F-062)

Structure for chaos. The tag library defines namespaces with rules:

**Closed namespaces** - only predefined values allowed:
- `status/draft`, `status/review`, `status/approved`
- `sensitivity/public`, `sensitivity/internal`

**Open namespaces** - any value allowed:
- `topic/machine-learning`, `topic/kubernetes`, `topic/whatever`

System namespaces come predefined; users create their own:

```bash
ragd library create "project" --closed --tags alpha beta gamma
ragd library add "project" delta  # Add another value
ragd library validate             # Check all tags in KB
```

## Technical Decisions

**SQLite Tables**: Each feature gets its own table(s) rather than stuffing everything into one. This keeps migrations simple and concerns separated.

**fnmatch for Wildcards**: Instead of regex, we use fnmatch patterns (`project/*`). It's what shell users expect and covers 95% of use cases.

**Factory Methods**: `TagSuggestion.from_keybert()` beats a generic constructor with 8 parameters. Source-specific factories ensure correct metadata.

## The 77-Test Gauntlet

Wrote 77 new tests for these three features:
- TagQuery edge cases (empty AND, nested wildcards)
- Suggestion workflow (add, confirm, reject, clear)
- Namespace validation (open vs closed, system protection)

All 1157 tests now pass. The test suite grows more valuable with each release.

## Looking Ahead

The tagging infrastructure is complete. Documents can be:
- **Tagged** with provenance (v0.8.0)
- **Organised** into smart collections (v0.8.1)
- **Suggested** for review (v0.8.1)
- **Validated** against namespaces (v0.8.1)

Next up: v0.8.2 brings retrieval enhancements - reranking and query decomposition. Better organisation means nothing if you can't find what you're looking for.

---

*~3 hours of autonomous implementation*
