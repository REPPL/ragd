# F-024: Basic WebUI

## Overview

**Research**: [State-of-the-Art User Interfaces](../../research/state-of-the-art-user-interfaces.md)
**Milestone**: v1.5
**Priority**: P2

## Problem Statement

CLI tools are powerful but intimidating for non-technical users. A basic web interface makes ragd accessible to everyone while maintaining the power of the CLI for advanced users. This also enables mobile/tablet access via browser.

## Design Approach

### Architecture

```
Browser
    ↓
FastAPI Server
    ├── REST API
    └── HTMX Frontend
    ↓
ragd Core (existing)
```

### Technologies

- **FastAPI**: Python web framework (async, fast, typed)
- **HTMX**: Minimal JavaScript, server-rendered
- **Tailwind CSS**: Utility-first styling
- **Jinja2**: Server-side templating
- **uvicorn**: ASGI server

### Design Principles

1. **Progressive enhancement**: Works without JavaScript
2. **Minimal complexity**: HTMX over React/Vue
3. **CLI parity**: All CLI features accessible
4. **Mobile-first**: Responsive design
5. **Local-first**: No cloud, no accounts

## Implementation Tasks

- [ ] Create FastAPI application structure
- [ ] Implement REST API for core operations
- [ ] Design HTMX-based frontend
- [ ] Create search interface
- [ ] Create index/upload interface
- [ ] Create status dashboard
- [ ] Create settings interface
- [ ] Add chat interface (v0.5 feature)
- [ ] Implement streaming responses
- [ ] Add onboarding flow
- [ ] Write API tests
- [ ] Write UI integration tests

## Success Criteria

- [ ] All core operations available via web
- [ ] Search works with real-time results
- [ ] Document upload functional
- [ ] Mobile-friendly responsive design
- [ ] Loads in < 2 seconds
- [ ] Works offline (after initial load)
- [ ] OpenAPI documentation generated

## Dependencies

- fastapi
- uvicorn
- jinja2
- python-multipart (file uploads)
- All core ragd features

## Technical Notes

### Configuration

```yaml
server:
  enabled: false  # Start with ragd serve
  host: 127.0.0.1  # Local only by default
  port: 8080
  cors_origins: []  # Empty = same-origin only

  security:
    api_key: null  # Optional API key
    rate_limit: 100  # requests per minute
```

### Project Structure

```
src/ragd/
├── api/
│   ├── __init__.py
│   ├── app.py           # FastAPI app
│   ├── routes/
│   │   ├── search.py
│   │   ├── index.py
│   │   ├── status.py
│   │   └── chat.py
│   └── templates/
│       ├── base.html
│       ├── search.html
│       ├── index.html
│       ├── status.html
│       └── chat.html
└── static/
    └── styles.css
```

### FastAPI Application

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="ragd",
    description="Personal knowledge management",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"))

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})
```

### Search API

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/search")

class SearchRequest(BaseModel):
    query: str
    k: int = 10
    mode: str = "hybrid"

class SearchResult(BaseModel):
    rank: int
    score: float
    source: str
    content: str
    metadata: dict

@router.post("/")
async def search(request: SearchRequest) -> list[SearchResult]:
    results = ragd.search(
        query=request.query,
        k=request.k,
        mode=request.mode
    )
    return [
        SearchResult(
            rank=i,
            score=r.score,
            source=r.metadata["source"],
            content=r.content,
            metadata=r.metadata
        )
        for i, r in enumerate(results, 1)
    ]
```

### HTMX Search Interface

```html
<form hx-post="/api/search"
      hx-target="#results"
      hx-indicator="#spinner">
  <input type="text"
         name="query"
         placeholder="Search your knowledge..."
         class="w-full p-4 border rounded">
  <button type="submit"
          class="mt-2 px-6 py-2 bg-blue-600 text-white rounded">
    Search
  </button>
</form>

<div id="spinner" class="htmx-indicator">
  Searching...
</div>

<div id="results">
  <!-- Results rendered here by HTMX -->
</div>
```

### CLI Command

```bash
# Start web server
ragd serve

# With options
ragd serve --port 8080 --host 0.0.0.0

# Open browser automatically
ragd serve --open
```

### Mobile-First CSS

```css
/* Base (mobile) */
.search-container {
  padding: 1rem;
  max-width: 100%;
}

/* Tablet and up */
@media (min-width: 768px) {
  .search-container {
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .search-container {
    max-width: 1000px;
  }
}
```

## Related Documentation

- [State-of-the-Art User Interfaces](../../research/state-of-the-art-user-interfaces.md) - Research basis
- [v1.5.0 Milestone](../../milestones/v1.5.0.md) - Release planning
- [CLI Best Practices](../../research/cli-best-practices.md) - CLI/Web consistency

---
