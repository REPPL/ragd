# ADR-0003: Privacy-First Architecture

## Status

Accepted

## Context

Users of personal knowledge systems handle sensitive data:
- Personal notes and journals
- Financial documents
- Medical records
- Work documents (potentially confidential)
- Research and intellectual property

Traditional RAG systems often rely on cloud APIs for:
- Embedding generation (OpenAI, Cohere)
- Vector storage (Pinecone, Weaviate Cloud)
- LLM inference (GPT-4, Claude)

This sends user data to third parties, creating privacy and security risks.

## Decision

ragd implements a **privacy-first architecture** where all processing happens locally by default.

### Core Principles

1. **No telemetry:** No usage data, analytics, or crash reports sent externally
2. **Local embeddings:** sentence-transformers runs on user's machine
3. **Local storage:** ChromaDB stores all data locally
4. **Local inference:** Ollama for LLM features (v0.5+)
5. **No external APIs:** No network requests during normal operation
6. **User owns data:** All data in user-accessible directories

### Data Flow

```
User Document
    ↓
[Local] Text Extraction
    ↓
[Local] Chunking
    ↓
[Local] Embedding (sentence-transformers)
    ↓
[Local] Storage (ChromaDB at ~/.ragd/)
    ↓
[Local] Search
    ↓
User Results
```

### Configuration

```yaml
# ~/.ragd/config.yaml
privacy:
  telemetry: false          # Cannot be enabled
  allow_network: false      # Default: no network requests
  local_models_only: true   # Enforce local model usage
```

## Consequences

### Positive

- Complete data privacy
- Works offline
- No subscription costs
- No API rate limits
- GDPR/compliance friendly
- User controls their data

### Negative

- Requires local compute resources (CPU/GPU)
- Initial model download requires internet
- May not match cloud API quality (smaller models)
- User responsible for backups

### Trade-offs Accepted

| Aspect | Cloud Approach | ragd Approach |
|--------|----------------|---------------|
| Quality | Best models | Good local models |
| Speed | API latency | Local, hardware-dependent |
| Cost | Per-token pricing | One-time compute cost |
| Privacy | Data sent externally | Complete privacy |
| Offline | Requires internet | Fully offline |

## Future Considerations

### Optional Cloud Features (v1.0+)

For users who explicitly opt-in, we may add:
- Cloud LLM integration (must be opt-in, not default)
- Cloud sync (encrypted, user-controlled keys)

Any cloud features must:
- Be disabled by default
- Require explicit opt-in
- Clearly explain what data is shared
- Provide local alternatives

## Alternatives Considered

### Cloud-First with Local Option

- **Pros:** Better initial experience, less setup
- **Cons:** Privacy compromise, vendor lock-in
- **Rejected:** Violates core principle

### Hybrid Default

- **Pros:** Balance of quality and privacy
- **Cons:** Confusing, privacy still compromised
- **Rejected:** Privacy must be the default

## Related Documentation

- [ragged Analysis](../../lineage/ragged-analysis.md) - Privacy-first inheritance
- [Acknowledgements](../../lineage/acknowledgements.md) - Local model citations

