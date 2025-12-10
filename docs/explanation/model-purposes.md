# Understanding Model Purposes in ragd

ragd uses different AI models for different tasks in the RAG pipeline. This document explains what each model purpose does, when it's used, and how to choose the right model for each role.

## The Five Model Purposes

ragd configures five distinct model purposes:

| Purpose | Config Path | Default | Used For |
|---------|-------------|---------|----------|
| **Chat** | `llm.model` | `llama3.2:3b` | Answering questions with retrieved context |
| **Summary** | `metadata.summary_model` | `llama3.2:3b` | Generating document summaries |
| **Classification** | `metadata.classification_model` | `llama3.2:3b` | Categorising documents by topic |
| **Embedding** | `embedding.model` | `all-MiniLM-L6-v2` | Converting text to vectors for search |
| **Contextual** | `retrieval.contextual.model` | `llama3.2:3b` | Enhancing chunks with document context |

## Chat Model

**What it does:** Generates answers to your questions using retrieved document chunks as context.

**When it's used:** Every time you run `ragd ask` or `ragd chat`.

**What makes a good chat model:**
- Strong instruction-following
- Good at synthesising information from multiple sources
- Coherent, well-structured responses
- Appropriate response length

**Recommended models:**
- `llama3.2:3b` — Fast, good quality, low resource usage
- `llama3.1:8b` — Higher quality, more nuanced responses
- `qwen2.5:7b` — Excellent reasoning, good for complex queries

**Configure with:**
```bash
ragd models set --chat llama3.1:8b
```

## Summary Model

**What it does:** Creates concise summaries of documents during indexing. These summaries help with search relevance and provide quick document overviews.

**When it's used:** During `ragd index` when processing new documents.

**What makes a good summary model:**
- Concise output (summaries should be brief)
- Good at identifying key points
- Accurate representation of content
- Fast inference (runs on every document)

**Recommended models:**
- `llama3.2:3b` — Good balance of quality and speed
- `phi3:mini` — Very fast, suitable for large document collections

**Configure with:**
```bash
ragd models set --summary llama3.2:3b
```

## Classification Model

**What it does:** Assigns topic categories and tags to documents during indexing. This enables filtering searches by document type or subject.

**When it's used:** During `ragd index` when processing new documents.

**What makes a good classification model:**
- Consistent categorisation
- Follows classification schemas
- Low hallucination rate
- Fast inference

**Recommended models:**
- `llama3.2:3b` — Reliable classification
- `phi3:mini` — Faster for large batches

**Configure with:**
```bash
ragd models set --classification llama3.2:3b
```

## Embedding Model

**What it does:** Converts text into numerical vectors (embeddings) that capture semantic meaning. These vectors enable semantic search—finding documents by meaning rather than exact keyword matches.

**When it's used:**
- During `ragd index` to embed document chunks
- During `ragd search`, `ragd ask`, and `ragd chat` to embed your query

**What makes a good embedding model:**
- High-quality semantic representations
- Consistent embedding space
- Appropriate dimension size for your storage
- Fast inference

**How it differs:** Unlike the other models, embedding models are typically not LLMs. They're specialised encoder models trained specifically for generating embeddings.

**Recommended models:**
- `all-MiniLM-L6-v2` — Default, good quality, 384 dimensions
- `all-mpnet-base-v2` — Higher quality, 768 dimensions
- `nomic-embed-text` — Ollama-hosted, good for GPU acceleration

**Configure with:**
```bash
ragd models set --embedding nomic-embed-text
```

> **Note:** Changing embedding models requires reindexing all documents, as different models produce incompatible vector spaces.

## Contextual Model

**What it does:** Enhances individual chunks with surrounding document context before embedding. This is part of [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)—a technique that improves search accuracy by adding context like "This chunk is from Chapter 3 discussing authentication methods in a security whitepaper."

**When it's used:** During `ragd index` when contextual retrieval is enabled (`retrieval.contextual.enabled: true`).

**What makes a good contextual model:**
- Concise context generation
- Understanding of document structure
- Fast inference (runs on every chunk)
- Low resource usage (many chunks to process)

**Recommended models:**
- `llama3.2:3b` — Good quality, reasonable speed
- `llama3.2:1b` — Faster, suitable when processing many documents
- `phi3:mini` — Very fast, good for large collections

**Configure with:**
```bash
ragd models set --contextual llama3.2:3b
```

## How Models Work Together

Here's how the models interact during typical ragd operations:

### During Indexing (`ragd index`)

```
Document → [Summary Model] → Summary stored
         → [Classification Model] → Categories stored
         → [Contextual Model*] → Context prepended to chunks
         → [Embedding Model] → Vectors stored

* Only if contextual retrieval is enabled
```

### During Search (`ragd ask`, `ragd chat`)

```
Query → [Embedding Model] → Query vector
      → Vector search → Retrieved chunks
      → [Chat Model] → Generated answer
```

## Choosing Models by Hardware

### Limited Resources (8GB RAM)
Use smaller, efficient models:
```bash
ragd models set --chat llama3.2:3b
ragd models set --summary phi3:mini
ragd models set --classification phi3:mini
ragd models set --contextual llama3.2:1b
```

### Standard Setup (16GB RAM)
Balance quality and speed:
```bash
ragd models set --chat llama3.2:3b
ragd models set --summary llama3.2:3b
ragd models set --classification llama3.2:3b
ragd models set --contextual llama3.2:3b
```

### High Performance (32GB+ RAM or GPU)
Prioritise quality:
```bash
ragd models set --chat llama3.1:8b
ragd models set --summary llama3.2:3b
ragd models set --classification llama3.2:3b
ragd models set --contextual llama3.2:3b
ragd models set --embedding all-mpnet-base-v2
```

## Viewing Current Configuration

See which models are configured for each purpose:
```bash
ragd models list
```

This shows two tables:
1. **Configured Models by Purpose** — Your current model assignments
2. **Available Ollama Models** — Models installed and ready to use

## Common Questions

### Can I use the same model for everything?

Yes. Many users configure the same LLM (e.g., `llama3.2:3b`) for chat, summary, classification, and contextual purposes. This simplifies setup and reduces memory usage since only one model needs to be loaded.

### Do I need all five models?

No. The embedding model is always required. The chat model is needed for `ragd ask` and `ragd chat`. Summary, classification, and contextual models are optional—they enhance functionality but ragd works without them.

### What happens if a model isn't installed?

ragd will show a warning and fall back to available models. Use `ragd models list` to see which models are installed, and `ollama pull <model>` to install missing ones.

### Why is embedding different from the others?

Embedding models are encoder-only transformers optimised for producing vector representations. LLMs are decoder models optimised for generating text. They serve fundamentally different purposes in the RAG pipeline.

---

## Related Documentation

- [Configuration Reference](../reference/configuration.md) — All configuration options
- [CLI Reference](../reference/cli-reference.md) — Command documentation
- [Contextual Retrieval Feature](../development/features/completed/F-010-contextual-retrieval.md) — Implementation details

