# Searching with ragd

Master search queries and result filtering.

**Time:** 20 minutes
**Level:** Beginner
**Prerequisites:** Completed Getting Started tutorial

## What You'll Learn

- Natural language queries
- Search modes (hybrid, semantic, keyword)
- Filtering and limiting results
- Output formats

## Basic Searching

Simple query:

```bash
ragd search "machine learning"
```

With more results:

```bash
ragd search "python tutorials" --limit 20
```

## Search Modes

### Hybrid Search (Default)

Combines semantic understanding with keyword matching:

```bash
ragd search "climate change impacts" --mode hybrid
```

Best for: General queries, natural questions

### Semantic Search

Pure vector similarity, understands concepts:

```bash
ragd search "global warming effects" --mode semantic
```

Best for: Conceptual queries, finding similar content

### Keyword Search

Pure BM25 matching, finds exact terms:

```bash
ragd search "TypeError: cannot subscript" --mode keyword
```

Best for: Error messages, exact phrases, technical terms

## Filtering Results

### By Score Threshold

Only show high-quality matches:

```bash
ragd search "API reference" --min-score 0.5
```

Lower threshold for broader results:

```bash
ragd search "API reference" --min-score 0.1
```

## Output Formats

### Rich (Default)

Coloured, interactive output:

```bash
ragd search "tutorial" --format rich
```

### Plain Text

For simple terminal output:

```bash
ragd search "tutorial" --format plain
```

### JSON

For scripting and automation:

```bash
ragd search "tutorial" --format json | jq '.results[0].content'
```

## Citations

Add citations to results:

```bash
ragd search "important findings" --cite apa
```

Available styles: none, inline, apa, mla, chicago, bibtex, markdown

## Non-Interactive Mode

Skip the navigator, print directly:

```bash
ragd search "query" --no-interactive
```

## Verification

You've succeeded if you can:
- [ ] Find documents using natural language
- [ ] Use different search modes effectively
- [ ] Filter results by score threshold
- [ ] Extract JSON output for scripting

## Next Steps

- [Chat Interface](03-chat-interface.md) - Interactive Q&A
- [Advanced Search](05-advanced-search.md) - Deeper search features

---

## Tips

- Use quotes for exact phrases: `"error code 500"`
- Try semantic mode for conceptual queries
- Try keyword mode for error messages
- Lower min-score if getting no results
