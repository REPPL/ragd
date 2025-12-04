# Advanced Search

Hybrid search tuning, contextual retrieval, and quality assessment.

**Time:** 30 minutes
**Level:** Advanced
**Prerequisites:** Completed basic tutorials

## What You'll Learn

- Tuning hybrid search weights
- Contextual retrieval for better accuracy
- Search quality evaluation
- Extraction quality assessment

## Hybrid Search Tuning

### Understanding Weights

Hybrid search combines semantic and keyword scores:

- **Semantic weight** - Understanding meaning (default: 0.7)
- **Keyword weight** - Matching exact terms (default: 0.3)

### Adjusting via Configuration

Edit `~/.ragd/config.yaml`:

```yaml
search:
  mode: hybrid
  semantic_weight: 0.7
  keyword_weight: 0.3
```

Or use interactive config:

```bash
ragd config --interactive
```

### When to Adjust

| Use Case | Recommendation |
|----------|----------------|
| Technical docs | More keyword (0.5/0.5) |
| General content | Default (0.7/0.3) |
| Conceptual queries | More semantic (0.8/0.2) |

## Contextual Retrieval

Improves search accuracy by adding AI-generated context to chunks.

### Enable Contextual Retrieval

Requires Ollama. Edit config:

```yaml
retrieval:
  contextual:
    enabled: true
    model: llama3.2:3b
```

### Re-index with Context

```bash
ragd reindex --all --contextual
```

### When to Use

- Research papers with complex relationships
- Technical documentation
- Documents with implicit context

## Evaluating Search Quality

### Single Query Evaluation

```bash
ragd evaluate --query "What is machine learning?"
```

### With Expected Answer

```bash
ragd evaluate \
    --query "What is machine learning?" \
    --expected "Machine learning is a subset of AI that enables systems to learn from data."
```

### Batch Evaluation

Create `test-queries.yaml`:

```yaml
queries:
  - query: "What is machine learning?"
    expected: "Machine learning is..."
  - query: "How does backpropagation work?"
    expected: "Backpropagation is..."
```

Run batch:

```bash
ragd evaluate --test-file test-queries.yaml
```

### LLM-Based Metrics

Include faithfulness and relevancy metrics:

```bash
ragd evaluate --query "..." --include-llm
```

## Extraction Quality

### Check Overall Quality

```bash
ragd quality
```

### Check Specific Document

```bash
ragd quality doc-123 --verbose
```

### Find Low-Quality Extractions

```bash
ragd quality --below 0.7
```

### Re-index Low Quality

```bash
ragd quality --below 0.7 --format json | \
    jq -r '.documents[].id' | \
    xargs -I{} ragd reindex {}
```

## Verification

You've succeeded if you can:
- [ ] Adjust search weights for your use case
- [ ] Enable and use contextual retrieval
- [ ] Evaluate search quality
- [ ] Identify and fix low-quality extractions

## Next Steps

- [Automation](06-automation.md) - Scripts and integrations

---

## Performance Tips

- Contextual retrieval increases indexing time
- Start with default weights, tune based on results
- Use batch evaluation to find optimal settings
