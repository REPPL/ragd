# v0.4.1 Retrospective

## Overview

**Milestone:** v0.4.1 - Boolean Search
**Agent:** Claude (claude-opus-4-5-20251101)
**Sessions:** Single extended conversation session
**Branch:** `main` (direct development)
**Date:** 2025-11-28

---

## What Happened

| Phase | Plan | Actual | Notes |
|-------|------|--------|-------|
| **Research** | State-of-the-art boolean search | Explored FTS5 capabilities | FTS5 native support discovered |
| **Parser Choice** | Evaluate options | pyparsing AST-based | User selected robust parser approach |
| **Implementation** | Query parser module | 6 files, ~985 lines | Clean modular design |
| **Integration** | Modify BM25 search | Graceful fallback added | Invalid queries fall back safely |
| **Testing** | Comprehensive coverage | 54 new tests (45 unit + 9 integration) | All pass |
| **Documentation** | Full suite | Tutorial, reference, milestone | User selected full docs |
| **Version Strategy** | v0.4.1 patch release | Released before v0.5.0 Chat | Avoids parallel agent conflicts |

## Features Completed

| Feature | Tests | Files | Notes |
|---------|-------|-------|-------|
| Boolean Operators (AND, OR, NOT) | 45 unit + 9 integration | `src/ragd/search/query/` | pyparsing grammar |
| Phrase Search (`"..."`) | Included above | `parser.py` | Exact phrase matching |
| Prefix Wildcards (`term*`) | Included above | `parser.py` | Word prefix matching |
| Grouped Expressions `()` | Included above | `parser.py` | Operator precedence control |
| Query Validation | Included above | `validator.py` | Warnings for edge cases |
| User-friendly Errors | Included above | `errors.py` | Position pointers, suggestions |
| Graceful Fallback | Included above | `bm25.py` | Invalid queries use simple search |

**Total:** 54 new tests for v0.4.1 features

## Manual Interventions Required

| Intervention | Cause | Resolution | Could Be Automated? |
|--------------|-------|------------|---------------------|
| **OR operator as word** | Grammar consumed OR before operator rule matched | Added negative lookahead `~AND + ~OR + ~NOT` | **No** - grammar design decision |
| **FTS5 NOT syntax** | Generated `A AND NOT B` rejected by FTS5 | Transformer detects AND+NOT, generates `A NOT B` | **Yes** - better FTS5 syntax research |
| **Test case sensitivity** | Expected "standalone NOT" vs "Standalone NOT" | Fixed test assertion | **Yes** - case-insensitive assertions |
| **AND test logic** | Test expected AND with separate chunks | Changed to OR which correctly matches | **Yes** - integration test design |

**Key Finding:** 3 of 4 interventions were test-related or syntax edge cases. The FTS5 NOT syntax issue required understanding SQLite's specific boolean syntax requirements.

## Documentation Drift

| Drift Type | Files Affected | Root Cause |
|------------|----------------|------------|
| None detected | 0 | Docs created alongside implementation |

**Pattern:** Following v0.3.0 retrospective recommendations, documentation was created during implementation rather than post-release. No drift occurred.

## Lessons Learned

### What Worked Well

- **Research-first approach**: Understanding FTS5's native boolean support before implementation prevented wasted effort
- **User decision points**: Asking user to choose between minimal/robust parser and doc scope ensured alignment
- **Comprehensive testing**: 45 unit tests caught grammar and transformer issues early
- **Graceful degradation**: Fallback to simple search prevents user frustration on malformed queries
- **Single session implementation**: All work completed in one extended session, avoiding context loss

### What Needs Improvement

- **FTS5 syntax research**: The `A AND NOT B` vs `A NOT B` issue could have been caught earlier with better FTS5 documentation review
- **Version coordination**: Initial work assumed v0.5.0 integration until user clarified v0.4.1 patch release strategy
- **Process docs before release**: Retrospective created post-release (this document) rather than before tagging

## Process Improvements Applied from v0.3.0

Based on v0.3.0 retrospective:

| Action Item | Status | Notes |
|-------------|--------|-------|
| Run `/verify-docs` before release | **Partially** | Ran post-release, found missing retrospective |
| Move feature docs immediately | N/A | No feature spec file for boolean search |
| Create implementation record | Not done | Could be added |
| Create retrospective before tag | **Not done** | This doc created post-tag |

## Technical Achievements

### Query Parser Module (`src/ragd/search/query/`)

- **AST Design**: `TermNode`, `BinaryNode`, `UnaryNode`, `GroupNode` dataclasses
- **pyparsing Grammar**: Negative lookahead for keyword exclusion, case-insensitive operators
- **FTS5 Transformer**: Converts AST to SQLite FTS5 query syntax
- **Validator**: Warns on standalone NOT, deep nesting
- **Error Messages**: Position pointers showing exactly where parsing failed

### Integration Approach

- **Minimal BM25 changes**: Only `_escape_query()` modified
- **Fallback safety**: `_simple_escape()` preserved for parse failures
- **CLI enhancement**: Boolean examples in help text, error display

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| pyparsing over regex | Complex nested expressions, better error reporting |
| Keyword mode only | Boolean operators make less sense for semantic similarity |
| Graceful fallback | Better UX than hard failures on malformed queries |
| Case-insensitive operators | User convenience (AND, and, And all work) |

## Metrics

| Metric | v0.4.0 | v0.4.1 | Change |
|--------|--------|--------|--------|
| Total tests | ~674 | 728 | +54 |
| New features | 1 (multi-modal) | 7 (boolean ops) | Focused scope |
| New files | ~10 | 6 | Query module |
| Lines added | ~1200 | ~2190 | Comprehensive |
| Documentation files | 1 | 3 | Tutorial, reference, milestone |

## Action Items for v0.5.0

Based on this retrospective:

1. [ ] Create retrospective **before** tagging release
2. [ ] Run `/verify-docs` **before** tagging release
3. [ ] Research target system (Ollama LLM) syntax quirks early
4. [ ] Document version coordination decisions upfront
5. [ ] Consider feature spec file for significant features

---

## Related Documentation

- [v0.4.1 Milestone](../../milestones/v0.4.1.md) - Release planning
- [Powerful Searching Tutorial](../../../tutorials/powerful-searching.md) - User guide
- [Search Syntax Reference](../../../reference/search-syntax.md) - Technical spec
- [v0.3.0 Retrospective](./v0.3.0-retrospective.md) - Previous milestone

---

**Status**: Complete
