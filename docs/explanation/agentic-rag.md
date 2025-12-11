# Understanding Agentic RAG

Agentic RAG adds self-correction to standard RAG, improving answer quality for complex questions.

## Standard RAG vs Agentic RAG

**Standard RAG:**
```
Question → Retrieve documents → Generate answer
```

**Agentic RAG:**
```
Question → Retrieve documents → Evaluate quality → (Rewrite query?) → Generate answer → Evaluate faithfulness → (Refine?)
```

The key difference: agentic RAG evaluates its own work and corrects mistakes.

## How It Works

### CRAG: Corrective RAG

CRAG addresses a common problem: sometimes retrieval fails. The documents found aren't actually relevant to the question.

**The Problem:**
```
Query: "authentication best practices"
Retrieved: documents about "authentic Italian cuisine"
Result: Irrelevant answer
```

**CRAG Solution:**
1. Retrieve documents for the query
2. Evaluate: "Are these documents relevant to the question?"
3. If relevance is low, rewrite the query
4. Retrieve again with the improved query
5. Proceed to generation

**Example:**
```
Original query: "authentication methods"
Evaluation: Low relevance (found cooking docs)
Rewritten query: "user login security methods"
New retrieval: High relevance security documents
```

### Self-RAG: Self-Reflective RAG

Self-RAG addresses a different problem: even with good retrieval, the AI might hallucinate or misrepresent sources.

**The Problem:**
```
Retrieved: "Revenue grew 5% in Q3"
Generated: "Revenue grew 15% in Q3"
Result: Hallucinated answer
```

**Self-RAG Solution:**
1. Generate initial answer from retrieved context
2. Evaluate: "Is this answer faithful to the sources?"
3. If faithfulness is low, refine the answer
4. Return answer with confidence score

## When to Use Agentic Mode

**Use `--agentic` when:**
- The question is complex or multi-part
- You need high confidence in accuracy
- Previous answers seemed off
- The question might be ambiguous
- You're making important decisions based on the answer

**Skip agentic mode when:**
- Simple factual queries ("What is the project name?")
- Speed is critical
- You're just exploring/browsing
- The question is very specific

## Usage

```bash
# Standard RAG (faster)
ragd ask "What is the project deadline?"

# Agentic RAG (more thorough)
ragd ask "Compare the three proposed solutions" --agentic

# With confidence score
ragd ask "What are the security recommendations?" --agentic --show-confidence
```

## Trade-offs

| Aspect | Standard RAG | Agentic RAG |
|--------|--------------|-------------|
| Speed | Fast | Slower (2-4x) |
| Accuracy | Good | Better |
| Token usage | Lower | Higher |
| Best for | Simple queries | Complex questions |

## Technical Details

### Relevance Evaluation
CRAG uses the LLM to rate document relevance on a scale:
- **High**: Documents directly answer the question
- **Medium**: Documents are related but incomplete
- **Low**: Documents are off-topic

When relevance is low, the system:
1. Analyses why retrieval failed
2. Identifies missing concepts
3. Generates alternative queries
4. Attempts retrieval again

### Faithfulness Evaluation
Self-RAG checks each claim against sources:
- Are facts supported by retrieved text?
- Are numbers accurately quoted?
- Are conclusions justified by evidence?

Low faithfulness triggers answer refinement or explicit uncertainty markers.

## Configuration

Agentic behaviour can be configured in `~/.ragd/config.yaml`:

```yaml
chat:
  agentic:
    enabled: false              # Default off, use --agentic flag
    max_rewrites: 2             # Maximum query rewrite attempts
    relevance_threshold: 0.5    # Minimum relevance before rewriting
    faithfulness_threshold: 0.7 # Minimum faithfulness before refining
```

---

## Related Documentation

- [What is RAG?](./what-is-rag.md) - RAG fundamentals
- [Command Comparison](../guides/cli/command-comparison.md) - When to use ask vs search vs chat
- [CLI Reference: ask](../reference/cli-reference.md#ragd-ask) - Complete ask command options
