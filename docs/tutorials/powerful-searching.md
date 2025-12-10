# Powerful Searching

Master ragd's search capabilities for finding exactly what you need.

**Time:** 20 minutes
**Level:** Intermediate
**Prerequisites:** Completed [Getting Started](01-getting-started.md) tutorial, indexed documents

## What You'll Learn

- Understanding semantic vs keyword search
- Choosing the right search mode
- Using citations in search results
- Filtering results by tags and metadata
- Interactive result navigation
- Optimising search for different use cases

## Understanding Search Modes

ragd offers three search modes, each with different strengths:

| Mode | Best For | How It Works |
|------|----------|--------------|
| **Hybrid** | General use (default) | Combines semantic + keyword |
| **Semantic** | Conceptual queries | Vector similarity matching |
| **Keyword** | Exact terms, names | Traditional BM25 matching |

### Hybrid Search (Default)

Combines the best of both approaches:

```bash
# Finds documents about the concept AND matching terms
ragd search "how does authentication work"
```

Hybrid search is the default because it handles most queries well—it finds conceptually related content while still prioritising exact matches.

### Semantic Search

Finds conceptually similar content, even when exact words differ:

```bash
# Finds documents about "authentication" even if they say "login", "sign-in", etc.
ragd search "user authentication" --mode semantic
```

**Use semantic when:**
- Searching for concepts, not specific terms
- You don't know the exact terminology used
- Looking for similar ideas across documents

### Keyword Search

Traditional exact-term matching:

```bash
# Only finds documents containing "OAuth2" exactly
ragd search "OAuth2" --mode keyword
```

**Use keyword when:**
- Searching for specific names, identifiers, or codes
- You know the exact terminology
- Looking for precise technical terms

## Step 1: Basic Search

Start with a natural language query:

```bash
ragd search "how to configure the application"
```

By default, ragd:
- Uses hybrid search mode
- Returns up to 10 results
- Opens an interactive navigator

### Interactive Navigation

The default view is an interactive navigator:

| Key | Action |
|-----|--------|
| `j` or `↓` | Next result |
| `k` or `↑` | Previous result |
| `Enter` | View full content |
| `q` | Quit navigator |

### Non-Interactive Output

For scripts or quick viewing:

```bash
ragd search "configuration" --no-interactive
```

## Step 2: Control Result Count

### Limit Results

```bash
# Get top 5 results
ragd search "machine learning" --limit 5

# Get more results
ragd search "neural networks" --limit 20
```

### Minimum Score Threshold

Filter out low-relevance results:

```bash
# Only show results with score >= 0.5
ragd search "transformers" --min-score 0.5

# Higher threshold for more precise results
ragd search "attention mechanism" --min-score 0.7
```

## Step 3: Add Citations

Include source citations in your results for reference or academic use.

### Citation Styles

```bash
# Inline citations: (filename, p. 3)
ragd search "research methodology" --cite inline

# APA format
ragd search "cognitive science" --cite apa

# MLA format
ragd search "literary analysis" --cite mla

# Chicago notes-bibliography
ragd search "historical events" --cite chicago

# BibTeX for LaTeX documents
ragd search "algorithms" --cite bibtex

# Markdown links
ragd search "documentation" --cite markdown
```

### Example Output with Citations

```
Result 1: Machine Learning Fundamentals
Score: 0.89
Content: "Neural networks are computational models inspired by..."
Citation: (ml-fundamentals.pdf, p. 12)
```

## Step 4: Search with Context

Use the `ask` command for question-answering with LLM synthesis:

```bash
# Get an AI-synthesised answer with sources
ragd ask "What are the main approaches to user authentication?"
```

The difference:
- `ragd search` - Returns matching document chunks
- `ragd ask` - Synthesises an answer from your documents using an LLM

## Step 5: Filter by Tags

Narrow your search to specific document collections:

```bash
# Search only in machine learning documents
ragd search "neural networks" --tag "topic:ml"

# Search in a specific project
ragd search "requirements" --tag "project:alpha"

# Search reviewed documents only
ragd search "conclusions" --tag "status:reviewed"
```

**Note:** Tag filtering uses the tags you've assigned with `ragd tag add`. See [Organising Your Knowledge Base](organising-knowledge-base.md) for tag management.

## Search Strategies

### Finding Conceptual Information

```bash
# Semantic mode for concept discovery
ragd search "how do transformers handle long sequences" --mode semantic
```

### Finding Specific Terms

```bash
# Keyword mode for exact matches
ragd search "BERT" --mode keyword
```

### Exploring a Topic

```bash
# Broad search, more results
ragd search "machine learning" --limit 20 --min-score 0.3
```

### Precise Retrieval

```bash
# Narrow search, high threshold
ragd search "attention is all you need" --limit 5 --min-score 0.7
```

### Research Citations

```bash
# Get results with academic citations
ragd search "neural network architectures" --cite apa --no-interactive
```

## Verification

You've succeeded if:
- [ ] `ragd search "test"` returns results from your documents
- [ ] Different modes (`--mode semantic`, `--mode keyword`) give different results
- [ ] `--limit` controls the number of results returned
- [ ] `--cite` adds citations to results
- [ ] Interactive navigator responds to `j`, `k`, `q` keys

## Example Workflow

```bash
# 1. Start with a broad search
ragd search "authentication"

# 2. Too many results? Add a tag filter
ragd search "authentication" --tag "project:alpha"

# 3. Looking for specific implementation? Use keyword mode
ragd search "OAuth2 implementation" --mode keyword

# 4. Need to cite sources? Add citation format
ragd search "authentication methods" --cite apa --no-interactive

# 5. Want an AI-synthesised answer?
ragd ask "What authentication methods does our system support?"
```

## Next Steps

- [Organising Your Knowledge Base](organising-knowledge-base.md) - Create tags for filtered searches
- [Processing Difficult PDFs](processing-difficult-pdfs.md) - Ensure PDFs are searchable

---

## Tips

1. **Start broad, then narrow** - Begin with hybrid mode, add filters if too many results
2. **Use tags for collections** - Pre-filter with tags for topic-specific searches
3. **Semantic for concepts** - When you want related ideas, not exact matches
4. **Keyword for precision** - When you know the exact terms
5. **Citations for research** - Use `--cite` when building references

---

## Troubleshooting

**No results found**
- Check spelling and try alternative terms
- Lower the `--min-score` threshold
- Try semantic mode for conceptual matching
- Verify documents are indexed: `ragd info`

**Too many irrelevant results**
- Increase `--min-score` threshold
- Add tag filters: `--tag "topic:..."`
- Use keyword mode for specific terms
- Narrow your query

**Results not matching expectations**
- Try different search modes
- Semantic mode may find unexpected but relevant content
- Check document quality: `ragd quality`

**Interactive navigator not working**
- Use `--no-interactive` for plain output
- Check terminal supports ANSI escape codes

---

## Related Documentation

- [Tutorial: Getting Started](01-getting-started.md)
- [F-005: Semantic Search](../development/features/completed/F-005-semantic-search.md)
- [F-012: Hybrid Search](../development/features/completed/F-012-hybrid-search.md)
- [F-009: Citation Output](../development/features/completed/F-009-citation-output.md)
