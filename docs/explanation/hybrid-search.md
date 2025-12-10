# Understanding Hybrid Search

ragd uses **hybrid search** to find relevant information by combining two complementary search techniques. This document explains how it works and why this approach produces better results than either technique alone.

## The Two Search Techniques

### Semantic Search

Semantic search finds documents based on **meaning**, not exact words.

**How it works:**
1. Your query is converted into a numerical vector (embedding) that captures its meaning
2. Document chunks have already been converted to vectors during indexing
3. ragd finds chunks whose vectors are mathematically similar to your query vector

**Strengths:**
- Understands synonyms ("car" matches "automobile")
- Handles paraphrasing ("how to fix bugs" matches "debugging techniques")
- Works well for conceptual questions

**Weaknesses:**
- Can miss exact terms (searching "RFC-7231" might not find the exact string)
- May retrieve semantically similar but irrelevant content
- Newer or domain-specific terms may not embed well

### Keyword Search (BM25)

Keyword search finds documents containing the **exact words** you searched for.

**How it works:**
1. ragd tokenises your query into individual terms
2. It searches for documents containing those terms
3. Results are scored using BM25 (a sophisticated term-frequency algorithm)

**Strengths:**
- Exact term matching (perfect for codes, names, acronyms)
- Predictable behaviour
- Fast and well-understood

**Weaknesses:**
- Misses synonyms ("car" won't match "automobile")
- Sensitive to word choice
- Can't understand context or intent

## Why Combine Them?

Neither technique is perfect alone:

| Query Type | Semantic | Keyword | Hybrid |
|------------|----------|---------|--------|
| "authentication methods" | Good | Moderate | Best |
| "RFC-7231" | Poor | Excellent | Best |
| "how do users log in" | Excellent | Poor | Best |
| "OAuth2 flow" | Good | Good | Best |

Hybrid search leverages the strengths of both approaches while mitigating their weaknesses.

## Reciprocal Rank Fusion (RRF)

ragd combines results using **Reciprocal Rank Fusion** (RRF), a technique that merges multiple ranked lists without requiring score normalisation.

### The Problem with Simple Averaging

You might think: "Just average the two scores." But this doesn't work because:
- Semantic scores (cosine similarity) range from -1 to 1, typically 0.3-0.9
- BM25 scores are unbounded positive numbers, often 5-50+
- A BM25 score of 20 isn't comparable to a semantic score of 0.8

### How RRF Works

Instead of combining scores, RRF combines **ranks**:

```
RRF_score(document) = Σ (1 / (k + rank))
```

Where:
- `rank` is the document's position in each search result list
- `k` is a constant (default: 60) that controls how much weight to give to lower-ranked results

**Example:**
- Document A: Rank 1 in semantic, Rank 5 in keyword
- Document B: Rank 3 in semantic, Rank 1 in keyword

RRF scores (with k=60):
- Document A: 1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318
- Document B: 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323

Document B wins slightly because being #1 in keyword compensates for being #3 in semantic.

### Why k=60?

The constant `k` determines how steeply relevance drops with rank:
- Lower k (e.g., 20): Top results dominate heavily
- Higher k (e.g., 100): More gradual decline, gives more weight to lower ranks

Research has shown k=60 works well across diverse datasets. ragd uses this default but allows configuration.

## Search Modes in ragd

ragd supports three search modes:

```bash
# Default: hybrid search (best for most queries)
ragd search "your query"

# Semantic only (when meaning matters more than exact terms)
ragd search "your query" --mode semantic

# Keyword only (when you need exact term matching)
ragd search "your query" --mode keyword
```

### When to Use Each Mode

| Mode | Best For |
|------|----------|
| **hybrid** (default) | General queries, unknown content |
| **semantic** | Conceptual questions, "how does X work" |
| **keyword** | Exact codes, names, error messages, acronyms |

## Configuration

### Weights

You can adjust the relative importance of each search type:

```yaml
# In ~/.ragd/config.yaml
search:
  semantic_weight: 0.7  # 70% emphasis on semantic
  keyword_weight: 0.3   # 30% emphasis on keyword
```

These weights affect which results appear when documents appear in only one search type's results.

### RRF Constant

```yaml
search:
  rrf_k: 60  # Default value
```

Lower values make top results more dominant; higher values spread weight more evenly.

## How Search Results Look

When you search, ragd shows you information about how each result was found:

```
[1] authentication.md (Score: 0.847)
    Semantic: #2, Keyword: #1

[2] oauth-guide.pdf (Score: 0.823)
    Semantic: #1, Keyword: #8
```

This transparency helps you understand why results appear in their order and whether to adjust your search strategy.

## Performance Considerations

Hybrid search is slightly slower than single-mode search because it runs both searches. However:
- Both searches run in parallel where possible
- The combination (RRF) is computationally trivial
- The quality improvement typically outweighs the small performance cost

For very large indexes (100,000+ documents), you might consider:
- Using `--mode semantic` for conceptual queries
- Using `--mode keyword` for exact-match queries
- Reserving hybrid for important searches

---

## Related Documentation

- [Configuration Reference](../reference/configuration.md) — Search configuration options
- [CLI Reference](../reference/cli-reference.md) — Search command documentation
- [Model Purposes](./model-purposes.md) — Understanding embedding models

