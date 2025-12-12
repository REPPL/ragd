# F-098: Advanced HTML Engine

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Current HTML extraction misses JavaScript-rendered content. Modern web pages often use SPAs (React, Vue) where content is dynamically loaded.

## Design Approach

Optional Playwright integration for JavaScript rendering with graceful fallback to static extraction.

### Architecture
```
HTML Input
    ↓
Static Check (BeautifulSoup)
    ↓
JS Detection? ──No──→ Static Extract
    ↓ Yes
Playwright Render ─Error─→ Static Fallback
    ↓
Dynamic Extract
```

### Configuration
```yaml
html:
  render_javascript: auto  # auto | always | never
  render_timeout: 30       # seconds
  wait_for_selector: null  # optional CSS selector
```

## Implementation Tasks

- [ ] Add Playwright optional dependency
- [ ] Create JSHTMLExtractor class
- [ ] Implement JavaScript detection heuristic
- [ ] Add render_javascript config option
- [ ] Add timeout and fallback handling
- [ ] Update HTML extractor to use JS rendering
- [ ] Document Playwright installation

## Success Criteria

- [ ] JS-rendered content extracted when enabled
- [ ] Graceful fallback on Playwright unavailable
- [ ] Configurable timeout and rendering options

## Dependencies

- playwright (optional)
- v0.8.7 (CLI Polish)

## Related Documentation

- [F-039: Advanced HTML Processing](./F-039-advanced-html-processing.md)
- [v0.9.6 Implementation](../../implementation/v0.9.6.md)

