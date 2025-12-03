# F-066: Configurable Chat Prompts

**Status**: Completed
**Version**: v0.7.0
**Priority**: Medium

---

## Problem Statement

The chat system uses hardcoded prompts with fixed citation instructions. Users cannot customise how the LLM is instructed to cite sources, leading to inconsistent citation behaviour across different use cases.

The default prompt was also weaker than needed: "cite when using information" rather than "Always cite your sources".

---

## Design Approach

### Changes Required

1. Add `ChatConfig` to `RagdConfig` for chat-specific settings
2. Add `ChatPromptsConfig` for customisable prompt elements
3. Update `PromptTemplate` to support dynamic citation instructions
4. Strengthen default chat prompt to require citations

### Configuration Structure

```yaml
chat:
  temperature: 0.7
  max_tokens: 1024
  context_window: 4096
  history_turns: 5
  search_limit: 5
  auto_save: true
  default_cite_mode: numbered
  prompts:
    citation_instruction: "Always cite your sources by referencing document names and page numbers."
```

---

## Implementation

### Files Modified

- `src/ragd/config.py` - Added `ChatPromptsConfig` and `ChatConfig` models
- `src/ragd/chat/prompts.py` - Added `with_citation_instruction()` method
- `src/ragd/chat/session.py` - Pass config citation instruction to templates

### New Configuration Classes

```python
class ChatPromptsConfig(BaseModel):
    """Configurable prompt settings for chat."""
    citation_instruction: str = (
        "Always cite your sources by referencing document names and page numbers."
    )

class ChatConfig(BaseModel):
    """Chat session configuration."""
    temperature: float = 0.7
    max_tokens: int = 1024
    context_window: int = 4096
    history_turns: int = 5
    search_limit: int = 5
    auto_save: bool = True
    default_cite_mode: str = "numbered"
    prompts: ChatPromptsConfig = Field(default_factory=ChatPromptsConfig)
```

### Template Enhancement

`PromptTemplate.with_citation_instruction()` creates a new template with custom citation text injected into the system prompt.

---

## Success Criteria

- [x] Citation instruction configurable via `config.yaml`
- [x] Default prompt strengthened to "Always cite"
- [x] `get_prompt_template()` accepts citation instruction parameter
- [x] Chat session uses config-defined instruction
- [x] All tests pass

---

## Dependencies

- F-065: Chat Citation Display (implemented together)
- Existing `RagdConfig` and `PromptTemplate` infrastructure

---

## Related Documentation

- [F-065: Chat Citation Display](./F-065-chat-citation-display.md)
- [Configuration Reference](../../../reference/configuration.md)

---

**Status**: Completed
