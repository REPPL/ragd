# Future Cloud Service Integration (v2.0+)

> **Status:** Not implemented. This document is a placeholder for future cloud service
> integration planned for v2.0 or later.

ragd is designed as a **local-first** RAG system. Cloud LLM and embedding services
are explicitly not supported until v2.0+.

---

## Planned Cloud Providers (v2.0+)

When implemented, ragd may support:

- **OpenAI** - GPT-4, text-embedding-3-small/large
- **Anthropic Claude** - claude-3-haiku, claude-3-sonnet
- **Cohere** - embed-v4
- **Voyage AI** - voyage-3, voyage-3-large
- **Google Gemini** - gemini-pro

---

## Configuration Preview

These configurations are **not yet implemented**. They are preserved here for future
reference when cloud integration is added in v2.0+.

### Embedding API Integration

```yaml
# NOT IMPLEMENTED - v2.0+ placeholder
embedding:
  api_models:
    voyage:
      enabled: false
      model: "voyage-3"
      api_key_env: "VOYAGE_API_KEY"

    openai:
      enabled: false
      model: "text-embedding-3-small"
      api_key_env: "OPENAI_API_KEY"
```

### LLM Provider Configuration

```yaml
# NOT IMPLEMENTED - v2.0+ placeholder
llm:
  provider: openai
  model: gpt-4
  # API key from environment: OPENAI_API_KEY

external_services:
  enable_web_search: true
  # Tavily key from environment: TAVILY_API_KEY
```

### API Key Management Pattern

```python
# NOT IMPLEMENTED - v2.0+ placeholder
import os
from typing import Optional

def get_api_key(service: str) -> Optional[str]:
    """Get API key from environment."""
    key = os.getenv(f"{service.upper()}_API_KEY")
    if not key:
        logger.warning(f"No API key found for {service}")
    return key

# Usage
openai_key = get_api_key("openai")
if openai_key:
    llm = OpenAI(api_key=openai_key)
```

---

## Related Documentation

- [ADR-0003: Privacy-First Architecture](../decisions/adrs/0003-privacy-first-architecture.md) - Why local-first is the default
- [State of the Art: Embeddings](../research/state-of-the-art-embeddings.md) - Embedding model comparison

---

**Status:** Placeholder - not implemented
