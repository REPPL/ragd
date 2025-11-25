# State-of-the-Art RAG Techniques for ragd Roadmap

Cutting-edge techniques not yet in ragged or ragd.

## Executive Summary

Recent advances in RAG (2024-2025) introduce significant improvements not captured in ragged's v0.1-v0.6 implementation. These techniques address key limitations: retrieval quality, evaluation, agentic reasoning, and graph-based knowledge representation.

---

## Technique 1: Agentic RAG (CRAG, Self-RAG)

**What It Is:**
- **Corrective RAG (CRAG)**: Evaluates retrieval quality before generation; if documents are irrelevant, triggers web search fallback or query rewriting
- **Self-RAG**: Uses reflection tokens to self-assess response quality; iteratively refines answers
- **Multi-agent collaboration**: Chain-of-Agents pattern from Google; decompose queries across specialised agents

**Why It Matters:**
- Addresses "garbage in, garbage out" - poor retrieval → poor generation
- 20-30% improvement in answer quality on complex queries
- Self-correction without human feedback

**Source**: [Agentic RAG Survey](https://arxiv.org/abs/2501.09136) (Jan 2025)

**Roadmap Position**: **v0.5 (Chat & Conversation)** or **v0.8 (Memory & Personalisation)**
- Fits naturally with Ollama LLM integration
- Requires generation capability before retrieval evaluation

**Implementation Sketch:**
```
Query → Retrieve → [Evaluate Relevance]
                        ↓ Low
                   [Rewrite Query] → Retrieve again
                        ↓ Still Low
                   [Web Search Fallback]
                        ↓
                   Generate → [Self-Assess] → [Refine if needed]
```

---

## Technique 2: Contextual Retrieval (Anthropic)

**What It Is:**
- Prepend context to each chunk before embedding
- Uses LLM to generate brief contextual summary for each chunk
- Combines with BM25 for hybrid search

**Why It Matters:**
- **67% reduction** in retrieval failures (top-20)
- **49% reduction** combined with hybrid search + reranking
- Solves the "chunk without context" problem

**Source**: [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (Sep 2024)

**Roadmap Position**: **v0.3 (Advanced Retrieval)**
- Fits with advanced chunking and hybrid search
- Requires embedding model for context generation

**Implementation Sketch:**
```
Document → Chunk → [Generate Context with LLM] → Embed(Context + Chunk) → Store
                   "This chunk is about user authentication
                    from the security documentation..."
```

**Cost Consideration:**
- LLM call per chunk (can use small/fast models)
- Claude Haiku or Ollama for local contextualisation

---

## Technique 3: Late Chunking (Jina AI)

**What It Is:**
- Use long-context embedding models (8K+ tokens)
- Embed entire document first, THEN chunk at embedding level
- Preserves cross-chunk context in embeddings

**Why It Matters:**
- Better context preservation than chunk-then-embed
- Works with existing embedding infrastructure
- No LLM cost (unlike Contextual Retrieval)

**Source**: [Jina AI Late Chunking](https://jina.ai/news/late-chunking-in-long-context-embedding-models/) (2024)

**Roadmap Position**: **v0.3 (Advanced Retrieval)** - Alternative to Contextual Retrieval
- jina-embeddings-v2-base-en supports 8K context
- Lower cost than LLM-based contextualisation

**Implementation Sketch:**
```
Document → Embed Full Document (long-context model) → Mean Pool per Chunk → Store
```

---

## Technique 4: GraphRAG / LightRAG

**What It Is:**
- **GraphRAG (Microsoft)**: Build knowledge graph from documents; use community detection; answer queries via graph + LLM
- **LightRAG**: Lightweight alternative with dual-level retrieval (entity + relationship)

**Why It Matters:**
- Handles multi-hop reasoning ("How does X relate to Y through Z?")
- Better for exploratory queries and knowledge discovery
- GraphRAG: 24-80% improvement on comprehensiveness

**Sources**:
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [LightRAG](https://arxiv.org/abs/2410.05779) (Oct 2024)

**Roadmap Position**: **v0.8 (Memory & Personalisation)** - Already planned with Kuzu
- Extends existing knowledge graph foundation
- Adds community detection and graph-based retrieval

**Implementation Sketch:**
```
Documents → Extract Entities → Build Graph (Kuzu) → Community Detection
Query → [Local Search: specific entities] + [Global Search: community summaries]
```

---

## Technique 5: ColBERT / Late Interaction

**What It Is:**
- Token-level embeddings instead of single vector per passage
- "Late interaction" - compute similarity at query time across all tokens
- RAGatouille: Easy ColBERT integration

**Why It Matters:**
- Better precision on keyword-specific queries
- Outperforms dense retrievers on out-of-domain queries
- Complementary to semantic search

**Source**: [RAGatouille](https://github.com/AnswerDotAI/RAGatouille)

**Roadmap Position**: **v0.3 (Advanced Retrieval)** - Optional backend
- Fits with hybrid search architecture
- Storage trade-off (more vectors per document)

**Implementation Sketch:**
```
Document → [Token Embeddings] → Store all token vectors
Query → [Token Embeddings] → MaxSim across all document tokens
```

---

## Technique 6: RAGAS Evaluation Framework

**What It Is:**
- Automated RAG quality metrics:
  - **Faithfulness**: Is the answer grounded in retrieved context?
  - **Answer Relevance**: Does the answer address the question?
  - **Context Precision**: Are retrieved docs relevant?
  - **Context Recall**: Were all relevant docs retrieved?

**Why It Matters:**
- Objective quality measurement without human labelling
- Enables automated testing and regression detection
- Industry standard for RAG evaluation

**Source**: [RAGAS Documentation](https://docs.ragas.io/)

**Roadmap Position**: **v0.5 (Chat)** or **v0.6 (Storage & Scalability)**
- Requires generation for full evaluation
- Can add retrieval-only metrics earlier

**Implementation Sketch:**
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

results = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])
```

---

## Technique 7: Long Context RAG (LongRAG)

**What It Is:**
- Use longer chunks (4K-8K tokens) instead of small chunks (256-512)
- Leverage long-context LLMs for comprehension
- Reduce retrieval errors by providing more context

**Why It Matters:**
- Models like Gemini (1M context), Claude (200K) make this viable
- Reduces chunking artifacts and boundary issues
- Simpler pipeline (fewer chunks to manage)

**Source**: [LongRAG Paper](https://arxiv.org/abs/2406.15319) (2024)

**Roadmap Position**: **v0.3 (Advanced Retrieval)** - Chunking strategy option
- Already planned: hierarchical chunking
- Add "long chunk" strategy for long-context models

**Trade-off:**
- More tokens per retrieval = higher LLM cost
- Better for local LLMs with fast inference

---

## Technique 8: Chain-of-Agents (Google)

**What It Is:**
- Multiple agents handle different aspects of a query
- Worker agents process chunks in parallel
- Manager agent synthesises responses

**Why It Matters:**
- Scalable to very long documents
- Better coherence on complex multi-part queries
- 10% improvement over single-agent RAG

**Source**: Google Research (2024)

**Roadmap Position**: **v0.8 (Memory)** or **post-v1.0**
- Requires robust LLM integration (v0.5)
- Adds complexity; benefits large knowledge bases

---

## Updated Roadmap Integration

| Technique | Target Version | Priority | Dependencies |
|-----------|----------------|----------|--------------|
| **Contextual Retrieval** | v0.3 | High | Ollama or embedding LLM |
| **Late Chunking** | v0.3 | High | Long-context embedding model |
| **ColBERT/RAGatouille** | v0.3 | Medium | Storage trade-off |
| **LongRAG Chunking** | v0.3 | Medium | Long-context LLM |
| **RAGAS Evaluation** | v0.5 | High | Generation capability |
| **CRAG (Corrective)** | v0.5 | Medium | Ollama LLM |
| **Self-RAG** | v0.5 | Medium | Ollama LLM |
| **GraphRAG/LightRAG** | v0.8 | Medium | Kuzu (already planned) |
| **Chain-of-Agents** | v1.1+ | Low | Multi-agent framework |

---

## Recommended Additions to ragd Milestones

**v0.3.0 - Advanced Retrieval** (existing milestone, enhanced):
- ADD: Contextual Retrieval OR Late Chunking (choose one initially)
- ADD: Long chunk strategy option
- CONSIDER: ColBERT as optional retrieval backend

**v0.5.0 - Chat & Conversation** (existing milestone, enhanced):
- ADD: RAGAS evaluation metrics
- ADD: Basic CRAG (retrieval quality check before generation)

**v0.8.0 - Memory & Personalisation** (existing milestone, enhanced):
- ENHANCE: Kuzu integration with GraphRAG patterns
- ADD: Community detection for knowledge graph
- CONSIDER: LightRAG as alternative to full GraphRAG

---

## Feature Specification Additions

**F-XXX: Contextual Retrieval**
```markdown
## Summary
Add contextual metadata to chunks before embedding to improve retrieval quality.

## Approach
- Use Ollama (or small Claude model) to generate brief context per chunk
- Prepend context to chunk before embedding
- Store original chunk separately for display

## Success Criteria
- [ ] Context generation for PDF chunks
- [ ] Configurable: enable/disable contextual retrieval
- [ ] Benchmark showing retrieval improvement

## Dependencies
- F-001: Document Ingestion
- F-005: Semantic Search
- Ollama integration (v0.5) OR API option
```

**F-XXX: RAGAS Integration**
```markdown
## Summary
Automated quality metrics for RAG responses.

## Approach
- Integrate ragas library
- Add `ragd evaluate` command
- Store evaluation history

## Success Criteria
- [ ] Faithfulness score for responses
- [ ] Context precision/recall metrics
- [ ] CLI command: `ragd evaluate --query "..." --answer "..."`

## Dependencies
- F-005: Semantic Search
- Chat capability (v0.5)
```

---

## Research Sources

| Technique | Source | Date |
|-----------|--------|------|
| Agentic RAG Survey | [arXiv:2501.09136](https://arxiv.org/abs/2501.09136) | Jan 2025 |
| GraphRAG | [Microsoft GitHub](https://github.com/microsoft/graphrag) | 2024 |
| LightRAG | [arXiv:2410.05779](https://arxiv.org/abs/2410.05779) | Oct 2024 |
| Contextual Retrieval | [Anthropic Blog](https://www.anthropic.com/news/contextual-retrieval) | Sep 2024 |
| Late Chunking | [Jina AI Blog](https://jina.ai/news/late-chunking-in-long-context-embedding-models/) | 2024 |
| RAGatouille | [GitHub](https://github.com/AnswerDotAI/RAGatouille) | 2024 |
| RAGAS | [Documentation](https://docs.ragas.io/) | 2024 |
| LongRAG | [arXiv:2406.15319](https://arxiv.org/abs/2406.15319) | Jun 2024 |

---

**State-of-the-Art Analysis Status**: Complete
