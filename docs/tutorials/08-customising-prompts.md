# Customising Prompts

Learn to modify ragd's AI behaviour by customising prompt templates.

**Time:** 20 minutes
**Level:** Advanced
**Prerequisites:** Completed [Chat Interface](./03-chat-interface.md)

## What You'll Learn

- Understanding ragd's prompt system
- Viewing available prompts
- Exporting prompts for customisation
- Modifying prompt behaviour

## Understanding Prompts

ragd uses prompt templates to guide how the AI responds. These templates control:

- **RAG prompts** - How answers are generated from retrieved context
- **Agentic prompts** - How the AI evaluates and refines queries
- **Metadata prompts** - How document metadata is extracted
- **Evaluation prompts** - How answer quality is assessed

## Viewing Available Prompts

List all prompt templates:

```bash
ragd prompts list
```

**Example output:**
```
Prompt Templates
────────────────

Category     Name
rag          answer
rag          no_context
agentic      relevance_eval
agentic      query_rewrite
metadata     title_extract
metadata     summary
evaluation   answer_quality
```

### Filter by Category

View only RAG prompts:

```bash
ragd prompts list --category rag
```

### Check Customisation Status

See which prompts have been customised:

```bash
ragd prompts list --status
```

**Output:**
```
Category     Name              Status
rag          answer            custom
rag          no_context        default
agentic      relevance_eval    default
```

## Viewing Prompt Content

See the full content of a specific prompt:

```bash
ragd prompts show rag/answer
```

This displays the template with variable placeholders like `{context}` and `{question}`.

## Exporting Prompts for Customisation

Export all prompts to files you can edit:

```bash
ragd prompts export
```

This creates files in `~/.ragd/prompts/`:

```
~/.ragd/prompts/
├── rag/
│   ├── answer.txt
│   └── no_context.txt
├── agentic/
│   ├── relevance_eval.txt
│   └── query_rewrite.txt
└── metadata/
    └── ...
```

### Export Specific Category

Export only RAG prompts:

```bash
ragd prompts export --category rag
```

### Custom Output Directory

Export to a different location:

```bash
ragd prompts export --output ~/my-prompts/
```

## Customising a Prompt

### Step 1: Export the Prompt

```bash
ragd prompts export --category rag
```

### Step 2: Edit the File

Open `~/.ragd/prompts/rag/answer.txt` in your editor:

```bash
nano ~/.ragd/prompts/rag/answer.txt
```

### Step 3: Modify the Template

**Original:**
```
Answer the question based on the following context.

Context:
{context}

Question: {question}

Answer:
```

**Customised (more concise responses):**
```
Based on the documents provided, give a brief, direct answer.
Use bullet points for multiple items. Cite sources as [1], [2], etc.

Documents:
{context}

Question: {question}

Brief Answer:
```

### Step 4: Save and Test

Save the file and test with:

```bash
ragd ask "What are the key points?"
```

Your customised prompt will be used automatically.

## Common Customisations

### More Concise Answers

Add instructions like:
- "Keep your answer under 3 sentences"
- "Use bullet points"
- "Be direct and factual"

### Academic Style

Add instructions like:
- "Use formal academic language"
- "Include page numbers in citations"
- "Acknowledge uncertainty appropriately"

### Technical Audience

Add instructions like:
- "Assume the reader has technical expertise"
- "Include code examples where relevant"
- "Use precise terminology"

### Non-Technical Audience

Add instructions like:
- "Explain concepts in simple terms"
- "Avoid jargon"
- "Use analogies to clarify complex ideas"

## Resetting to Defaults

To restore default prompts:

1. Delete the customised file:
   ```bash
   rm ~/.ragd/prompts/rag/answer.txt
   ```

2. Or overwrite with defaults:
   ```bash
   ragd prompts export --overwrite
   ```

## Verification

You've succeeded if you can:
- [ ] List available prompts with `ragd prompts list`
- [ ] View a prompt's content with `ragd prompts show`
- [ ] Export prompts with `ragd prompts export`
- [ ] Customise a prompt and see the change in responses

## Tips

- **Test incrementally** - Make small changes and test
- **Keep originals** - Export defaults before editing
- **Use placeholders** - Always include `{context}` and `{question}`
- **Be specific** - Clear instructions get better results

---

## Related Documentation

- [CLI Reference: prompts](../reference/cli-reference.md#ragd-prompts) - Full command options
- [Customising Prompts Guide](../guides/customising-prompts.md) - Detailed customisation guide
- [What is RAG?](../explanation/what-is-rag.md) - Understanding RAG prompts

---
