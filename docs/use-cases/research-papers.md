# Use Case: Research Papers

Academic research and paper management with ragd.

## Scenario

You're a researcher with hundreds of PDFs. You want to:
- Search across all papers by concept
- Find citations and related work
- Remember key findings across your library

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/research

chunking:
  strategy: recursive
  chunk_size: 1024  # Larger for academic text
  overlap: 100

search:
  mode: hybrid
  semantic_weight: 0.7

retrieval:
  contextual:
    enabled: true  # Better for academic content
```

### Initial Indexing

```bash
ragd index ~/Papers --recursive
```

Index Zotero storage:
```bash
ragd index ~/Zotero/storage
```

## Workflow

### Literature Review

```bash
ragd search "neural network architectures for time series"
```

### Finding Citations

```bash
ragd search "transformer attention mechanism original paper" --cite apa
```

### Cross-Paper Analysis

```bash
ragd chat --cite numbered
> Compare the methodologies in papers about BERT fine-tuning
```

### Organising Your Library

```bash
ragd tag add paper-123 "topic:nlp" "method:transformer"
ragd collection create nlp-papers --tag "topic:nlp"
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "state of the art in image segmentation" | Find recent advances |
| "papers that cite attention is all you need" | Related work |
| "experimental setup for NLP benchmarks" | Methodology details |
| "limitations mentioned in GPT papers" | Critical analysis |
| "datasets used for sentiment analysis" | Resource finding |

## Tips

1. **Enable contextual retrieval** - Academic text benefits from context
2. **Larger chunks** - Academic papers need more context (1024+)
3. **Use citations** - `--cite apa` for proper references
4. **Tag methodology** - Tag by method, topic, year
5. **Chat for synthesis** - Use chat to compare across papers

## Sample Research Session

```bash
# Find papers about your topic
ragd search "attention mechanisms in computer vision"

# Get citations
ragd search "vision transformer original paper" --cite bibtex

# Synthesise across papers
ragd chat
> What are the main approaches to handling long sequences in transformers?

# Find related datasets
ragd search "benchmark datasets used in papers"
```

---

## Related Use Cases

- [Personal Notes](personal-notes.md) - Note management
- [Code Documentation](code-documentation.md) - Technical docs
