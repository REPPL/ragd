# Understanding Contextual Retrieval

Contextual retrieval is a technique that dramatically improves search accuracy by adding document context to each chunk before embedding. This document explains the problem it solves and how ragd implements it.

## The Lost Context Problem

When ragd indexes a document, it splits it into smaller pieces called "chunks." This is necessary because:
- Embedding models have token limits
- Smaller chunks enable precise retrieval
- LLMs work better with focused context

But chunking creates a problem: **chunks lose their surrounding context.**

### Example: The Ambiguous Chunk

Consider this chunk from a financial report:

> "The company increased revenue by 15% compared to the previous quarter."

This chunk is ambiguous:
- Which company?
- Which quarter?
- What year?

The original document might have a header "Q3 2024 Financial Summary - Acme Corp" but that context is lost after chunking.

When you search for "Acme revenue growth," this chunk might not rank highly because it doesn't contain "Acme" anywhere.

## How Contextual Retrieval Solves This

Contextual retrieval adds a brief context summary to each chunk before embedding:

**Before (traditional chunking):**
> "The company increased revenue by 15% compared to the previous quarter."

**After (contextual retrieval):**
> "This excerpt is from Acme Corp's Q3 2024 financial report, discussing quarterly performance metrics. The company increased revenue by 15% compared to the previous quarter."

Now when you search for "Acme revenue growth," this chunk will rank highly because:
1. The context mentions "Acme"
2. The semantic meaning connects to revenue and growth
3. The temporal context (Q3 2024) is preserved

## How ragd Implements Contextual Retrieval

### During Indexing

When contextual retrieval is enabled:

```
Document → Chunk 1, Chunk 2, Chunk 3...
                ↓
          LLM generates context for each chunk
                ↓
          Context + Chunk combined
                ↓
          Combined text embedded
                ↓
          Stored in vector database
```

### The Context Generation Prompt

ragd uses an LLM to generate context. The default prompt asks for:
- What the text is about
- Where it comes from in the document
- Any relevant metadata (document type, section, etc.)

The generated context is:
- Brief (1-2 sentences)
- Factual (no interpretation)
- Specific (mentions document name, section, topic)

### Example Context Generation

**Input chunk:**
> "Users must authenticate using OAuth 2.0 before accessing protected resources."

**Document metadata:**
- Filename: api-security-guide.pdf
- Type: PDF
- Section: Chapter 3

**Generated context:**
> "This text is from the API Security Guide, Chapter 3, discussing authentication requirements for API access."

**Combined (what gets embedded):**
> "This text is from the API Security Guide, Chapter 3, discussing authentication requirements for API access. Users must authenticate using OAuth 2.0 before accessing protected resources."

## Enabling Contextual Retrieval

### Configuration

```yaml
# In ~/.ragd/config.yaml
retrieval:
  contextual:
    enabled: true
    provider: ollama
    model: llama3.2:3b
    timeout_seconds: 60
```

### CLI

```bash
# Enable during indexing
ragd index ~/Documents/ --contextual

# Configure the model
ragd models set --contextual llama3.2:3b
```

### Requirements

Contextual retrieval requires:
- An LLM (typically via Ollama)
- Additional processing time during indexing
- No additional resources at search time

## Performance Impact

### Indexing Time

Contextual retrieval adds LLM inference for each chunk:

| Collection Size | Without Contextual | With Contextual |
|----------------|-------------------|-----------------|
| 100 documents | ~2 minutes | ~10 minutes |
| 1,000 documents | ~20 minutes | ~2 hours |
| 10,000 documents | ~3 hours | ~20 hours |

Times vary significantly based on:
- Hardware (GPU vs CPU)
- Model size
- Document complexity
- Chunk size

### Search Quality

Research shows contextual retrieval improves retrieval accuracy significantly:
- Up to 67% reduction in failed retrievals (Anthropic research)
- Particularly effective for:
  - Technical documentation
  - Reports with structure
  - Documents with headers/sections
  - Content where context matters

### Storage

Contextual retrieval increases storage slightly:
- Each chunk stores the generated context (typically 50-200 characters)
- Embeddings remain the same size
- Overall increase: ~5-10%

## When to Use Contextual Retrieval

### Recommended For

- **Technical documentation** — API docs, manuals, specifications
- **Structured reports** — Financial reports, research papers
- **Legal documents** — Contracts, policies with sections
- **Large document collections** — Where precision matters

### May Not Be Necessary For

- **Simple text files** — Notes, logs without structure
- **Already contextual content** — Blog posts that self-reference
- **Speed-critical indexing** — When immediate availability matters
- **Limited hardware** — When LLM inference is slow

## Contextual Retrieval vs Late Chunking

Both techniques address the lost context problem but work differently:

| Aspect | Contextual Retrieval | Late Chunking |
|--------|---------------------|---------------|
| **When** | Indexing time | Embedding time |
| **How** | LLM generates context text | Transformer sees full document |
| **Requires** | LLM (Ollama) | Long-context embedding model |
| **Storage** | Slightly larger | Same |
| **Reindexing** | Needed if prompt changes | Needed if model changes |

**Can they be combined?** Yes, but with diminishing returns. Start with one, measure improvement, then consider adding the other if needed.

## Troubleshooting

### "Context generation is slow"

- Use a smaller model: `ragd models set --contextual llama3.2:1b`
- Increase batch size in config
- Consider GPU acceleration

### "Contexts seem generic"

- Try a larger model for better understanding
- Custom prompt template (advanced configuration)

### "Search results haven't improved"

- Verify contextual retrieval is enabled: `ragd info --detailed`
- Reindex documents after enabling: `ragd reindex`
- Test with structured documents first

---

## Related Documentation

- [Model Purposes](./model-purposes.md) — Understanding the contextual model
- [Configuration Reference](../reference/configuration.md) — Contextual retrieval settings
- [Hybrid Search](./hybrid-search.md) — How search works with contextual chunks

