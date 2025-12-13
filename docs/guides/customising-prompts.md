# Customising Prompts

This guide explains how to customise the prompts ragd uses for various operations, giving you control over response style, evaluation criteria, and more.

## Overview

ragd uses prompts for:

- **RAG prompts**: Answer generation, summarisation, comparison
- **Agentic prompts**: CRAG relevance evaluation, query rewriting, Self-RAG faithfulness
- **Metadata prompts**: Document summary and classification
- **Evaluation prompts**: Quality metrics (faithfulness, answer relevancy)

All prompts can be customised via:
1. Prompt files in `~/.ragd/prompts/`
2. Inline configuration in `~/.config/ragd/config.yaml`

## Quick Start

Export all default prompts for customisation:

```bash
ragd prompts export
```

This creates prompt files in `~/.ragd/prompts/` that you can edit.

## Prompt Commands

### List Available Prompts

```bash
# List all prompt templates
ragd prompts list

# List prompts in a specific category
ragd prompts list --category rag
ragd prompts list --category agentic

# Show which prompts have custom overrides
ragd prompts list --status
```

### Export Prompts

```bash
# Export all default prompts
ragd prompts export

# Export only a specific category
ragd prompts export --category rag

# Overwrite existing files
ragd prompts export --overwrite
```

### View Prompt Content

```bash
# View a specific prompt
ragd prompts show rag/answer
ragd prompts show agentic/relevance_eval
```

## Prompt Categories

### RAG Prompts (`rag/`)

| Prompt | Purpose |
|--------|---------|
| `answer` | Main answer generation from context |
| `summarise` | Document summarisation |
| `compare` | Multi-document comparison |
| `chat` | Conversational RAG responses |
| `refine` | Answer refinement for Self-RAG |

### Agentic Prompts (`agentic/`)

| Prompt | Purpose |
|--------|---------|
| `relevance_eval` | Evaluate context relevance (CRAG) |
| `query_rewrite` | Rewrite queries for better retrieval |
| `faithfulness_eval` | Evaluate answer faithfulness (Self-RAG) |

### Metadata Prompts (`metadata/`)

| Prompt | Purpose |
|--------|---------|
| `summary` | Generate document summaries |
| `classification` | Classify document type |
| `context` | Generate contextual chunk descriptions |

### Evaluation Prompts (`evaluation/`)

| Prompt | Purpose |
|--------|---------|
| `faithfulness` | RAGAS-style faithfulness scoring |
| `answer_relevancy` | RAGAS-style relevancy scoring |

## Configuration Methods

### Method 1: File-Based (Recommended)

1. Export the prompt you want to customise:
   ```bash
   ragd prompts export --category rag
   ```

2. Edit the file at `~/.ragd/prompts/rag/answer.txt`

3. Reference it in your config:
   ```yaml
   rag_prompts:
     answer:
       file: ~/.ragd/prompts/rag/answer.txt
   ```

### Method 2: Inline Configuration

For small tweaks, use inline configuration:

```yaml
rag_prompts:
  answer:
    inline: |
      You are a helpful assistant. Answer the question based only on the
      provided context. If the context doesn't contain relevant information,
      say so clearly.

      Context:
      {context}

      Question: {question}

      Answer:
```

### Prompt Variables

Prompts use Python format string variables:

| Variable | Description | Available In |
|----------|-------------|--------------|
| `{context}` | Retrieved document context | RAG, agentic |
| `{question}` | User's question | RAG, agentic |
| `{answer}` | Generated answer | Evaluation |
| `{history}` | Conversation history | Chat |
| `{text}` | Document text | Metadata |

## Interactive Configuration

Use the config wizard for prompt management:

```bash
ragd config --interactive
```

Select "Prompt templates" to:
- List all prompts
- Export prompts for customisation
- View customisation status
- Preview prompt content

## Best Practices

### Evaluation Prompts

Evaluation prompts should return a numeric score. The expected format is:

```
Score only a decimal between 0.0 and 1.0.
```

Example evaluation prompt:
```
Evaluate how well the answer addresses the question.

Question: {question}
Answer: {answer}

Rate from 0.0 (completely irrelevant) to 1.0 (perfectly relevant).
Respond with ONLY the score.
```

### RAG Prompts

Include clear instructions about:
- Using only provided context
- Handling missing information
- Citation format expectations

### Testing Custom Prompts

After customising a prompt:

```bash
# Test with a simple query
ragd ask "What is your purpose?" --verbose

# Check agentic behaviour
ragd ask "Complex question" --agentic --show-confidence

# Run evaluation to check metrics
ragd evaluate --query "Test query" --include-llm
```

## Troubleshooting

### Prompt Not Loading

Check the file path in config:
```bash
ragd config --show | grep prompts
```

Verify the file exists:
```bash
ls -la ~/.ragd/prompts/
```

### Invalid Prompt Format

Ensure prompt files:
- Use UTF-8 encoding
- Include required variables (e.g., `{context}`, `{question}`)
- Don't have syntax errors in format strings

### Resetting to Defaults

Remove the custom file and config reference, or use:
```bash
ragd prompts export --overwrite
```

Then remove the config override to use the built-in default.

---

## Related Documentation

- [Configuration Reference](../reference/config.example.yaml) - Full config options
- [CLI Reference](cli/reference.md) - Command documentation
- [Agentic RAG](../explanation/agentic-rag.md) - How CRAG and Self-RAG work
