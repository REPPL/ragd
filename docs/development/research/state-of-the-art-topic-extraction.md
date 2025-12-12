# State-of-the-Art Topic Extraction for RAG Systems

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

Techniques for automatically extracting topics from document corpora to enable tagging, taxonomy generation, and knowledge base overview in RAG systems.

## Executive Summary

Topic extraction has evolved from traditional statistical methods (LDA, NMF) to transformer-based approaches (BERTopic, KeyBERT) and LLM-powered solutions. The current best practice is a **hybrid tiered architecture**:

1. **BERTopic** for corpus-wide unsupervised topic discovery
2. **KeyBERT** for document-level keyword/tag extraction
3. **LLM** for human-readable topic labelling and taxonomy refinement

Key insights (2024-2025):
- **BERTopic outperforms LDA by 34%+** in clustering coherence (Springer 2024)
- **Claude 3.5 Sonnet leads zero-shot classification** with 0.76 F1 (February 2025)
- **Hybrid LDA+LLM reduces API costs** from hundreds of calls to one per corpus
- **Taxonomy-guided extraction reduces hallucinations by 23%** (ACL 2025)

### Decision Matrix: When to Use Each Approach

| Use Case | Recommended Approach | Why |
|----------|---------------------|-----|
| **Discover themes in new corpus** | BERTopic | Unsupervised, finds unknown topics |
| **Tag individual documents** | KeyBERT | Fast, no training, good keywords |
| **Classify into known categories** | Zero-shot LLM | High accuracy, flexible vocabulary |
| **Generate human-readable labels** | LLM topic labelling | Natural language understanding |
| **Build topic hierarchy** | LLM + taxonomy templates | Structured, consistent output |
| **Production at scale** | BERTopic + KeyBERT (local) | Cost-effective, no API limits |

---

## 1. Traditional Topic Modelling (Context)

Traditional methods remain relevant for resource-constrained environments and large-scale batch processing.

### Technique Overview

| Method | Approach | Pros | Cons |
|--------|----------|------|------|
| **LDA** (Latent Dirichlet Allocation) | Probabilistic bag-of-words | Interpretable, scalable, well-understood | No semantics, manual topic count |
| **NMF** (Non-Negative Matrix Factorisation) | Matrix factorisation | Sparse representations, fast | Similar limitations to LDA |
| **LSI/LSA** (Latent Semantic Indexing) | Singular value decomposition | Handles synonyms, polysemy | Dense representations, less interpretable |

### LDA Limitations Addressed by Modern Methods

1. **Bag-of-words assumption:** Ignores word order and context
2. **Fixed topic count:** Must specify K topics in advance
3. **Topic independence:** Assumes topics are uncorrelated
4. **No semantic understanding:** "bank" (financial) and "bank" (river) treated equally
5. **Preprocessing burden:** Requires extensive stopword removal, stemming

### When Traditional Methods Are Still Appropriate

- **Very large corpora (>1M documents):** BERTopic's embedding step becomes expensive
- **Resource-constrained environments:** LDA runs on minimal hardware
- **Baseline comparison:** Establishing performance benchmarks
- **Real-time streaming:** LDA updates incrementally; BERTopic requires batch retraining

**Source:** [ScienceDirect: Comprehensive Overview of Topic Modeling](https://www.sciencedirect.com/science/article/abs/pii/S0925231225003108)

---

## 2. BERTopic (Unsupervised Topic Discovery)

BERTopic is the current state-of-the-art for unsupervised topic modelling, consistently outperforming LDA in recent benchmarks.

### Architecture

```
Documents → BERT Embeddings → UMAP Dimensionality Reduction → HDBSCAN Clustering → c-TF-IDF Topic Representation
```

**Pipeline stages:**

1. **Embedding:** Sentence-transformers encode documents as dense vectors
2. **Dimensionality reduction:** UMAP projects to lower dimensions while preserving structure
3. **Clustering:** HDBSCAN finds dense regions (topics) without specifying K
4. **Representation:** c-TF-IDF extracts topic keywords from clusters

### Comparative Performance (2024-2025)

| Study | Finding | Source |
|-------|---------|--------|
| Springer 2024 | BERTopic **34.2% better** than LDA/Top2Vec in Chinese/English clustering | [Experimental Comparison](https://link.springer.com/chapter/10.1007/978-981-99-9109-9_37) |
| Ma et al. 2025 | BERTopic clusters "more compact and well-separated" in t-SNE visualisation | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11906279/) |
| Amazon Reviews 2024 | BERTopic "more meaningful results according to consistency metric" | [Springer](https://link.springer.com/chapter/10.1007/978-3-031-53717-2_3) |
| NY Times Study | BERTopic achieved "better topic separation, more independence between topics" | [Pacific Int'l Journal](https://rclss.com/pij/article/view/616) |

### Basic Implementation

```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

# Use existing ragd embedding model for consistency
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Create and fit model
topic_model = BERTopic(embedding_model=embedding_model)
topics, probs = topic_model.fit_transform(documents)

# Get topic info
topic_info = topic_model.get_topic_info()
# DataFrame with Topic, Count, Name, Representation (keywords)

# Get topics for specific documents
doc_topics = topic_model.get_document_info(documents)
```

### LLM Integration for Topic Labelling

BERTopic supports LLM-powered topic representation for human-readable labels:

```python
from bertopic.representation import OpenAI
import openai

# Configure LLM representation
client = openai.OpenAI(api_key="your-key")
representation_model = OpenAI(
    client,
    model="gpt-4o-mini",
    prompt="I have a topic with the following keywords: [KEYWORDS]. Based on these keywords, what is this topic about? Give a short label."
)

# Create model with LLM labelling
topic_model = BERTopic(representation_model=representation_model)
```

**Local LLM alternative (Ollama):**

```python
from bertopic.representation import LlamaCPP

# Use local Ollama model
representation_model = LlamaCPP(
    model_path="path/to/llama.gguf",
    prompt="Topic keywords: [KEYWORDS]. Short topic label:"
)
```

**Source:** [BERTopic LLM Integration](https://maartengr.github.io/BERTopic/getting_started/representation/llm.html)

### Integration with ragd Embedding Pipeline

ragd already uses sentence-transformers for document embedding. BERTopic can reuse these embeddings:

```python
# ragd pattern: reuse existing embeddings
from ragd.embedding import SentenceTransformerEmbedder

embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")

# Pre-compute embeddings (ragd already does this during indexing)
embeddings = embedder.embed(documents)

# Pass pre-computed embeddings to BERTopic
topic_model = BERTopic()
topics, probs = topic_model.fit_transform(documents, embeddings=embeddings)
```

### Computational Requirements

| Corpus Size | Embedding Time | Clustering Time | Memory |
|-------------|----------------|-----------------|--------|
| 1K docs | ~10s | ~2s | ~500MB |
| 10K docs | ~1-2 min | ~30s | ~2GB |
| 100K docs | ~15-20 min | ~5 min | ~8GB |
| 1M docs | Hours | ~1 hour | ~32GB+ |

**Recommendations:**
- Use GPU for embedding (CUDA/MPS) for 10x speedup
- Pre-compute embeddings during ragd indexing
- Consider incremental updates for dynamic corpora

---

## 3. KeyBERT (Keyword/Tag Extraction)

KeyBERT extracts keywords and keyphrases from individual documents using BERT embeddings—ideal for document-level tagging.

### How It Works

```
Document → BERT Embedding → N-gram Candidates → Cosine Similarity → Top Keywords
```

1. **Document embedding:** Encode full document as single vector
2. **Candidate extraction:** Generate n-gram candidates (e.g., 1-2 word phrases)
3. **Candidate embeddings:** Encode each candidate
4. **Similarity ranking:** Find candidates most similar to document embedding
5. **Diversity (optional):** MMR or Max Sum for keyword diversity

### Basic Implementation

```python
from keybert import KeyBERT

# Initialise with same model as ragd embeddings
kw_model = KeyBERT(model="all-MiniLM-L6-v2")

# Extract keywords
keywords = kw_model.extract_keywords(
    document,
    keyphrase_ngram_range=(1, 2),  # Unigrams and bigrams
    stop_words="english",
    top_n=10,
    use_mmr=True,  # Maximal Marginal Relevance for diversity
    diversity=0.5
)
# Returns: [("machine learning", 0.89), ("neural network", 0.82), ...]
```

### KeyLLM Extension (2024)

KeyLLM integrates LLMs for improved keyword extraction:

```python
from keybert.llm import OpenAI
from keybert import KeyLLM

# LLM-powered keyword extraction
llm = OpenAI()
kw_model = KeyLLM(llm)

keywords = kw_model.extract_keywords(
    documents,
    threshold=0.5  # Similarity threshold for grouping
)
```

**Benefits:**
- Better understanding of context and intent
- Can generate keywords not present in text
- Handles domain-specific terminology better

### Current ragd Integration

ragd already integrates KeyBERT in `MetadataExtractor`:

```python
# src/ragd/metadata/extractor.py
class MetadataExtractor:
    def extract_keywords(self, text: str) -> list[ExtractedKeyword]:
        """Extract keywords using KeyBERT if available."""
        if not self._enable_keywords or not KEYBERT_AVAILABLE:
            return []

        keywords = self._keybert.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            top_n=10,
            use_mmr=True
        )
        return [
            ExtractedKeyword(keyword=kw, score=score)
            for kw, score in keywords
        ]
```

### Enhancement Opportunities

1. **Configurable n-gram range:** Allow users to set phrase length
2. **Domain seeding:** Bias towards domain vocabulary
3. **Confidence thresholds:** Filter low-confidence keywords
4. **Caching:** Cache embeddings for batch processing

**Source:** [KeyBERT GitHub](https://github.com/MaartenGr/KeyBERT), [KeyBERT Documentation](https://maartengr.github.io/KeyBERT/)

---

## 4. LLM-Based Topic Extraction

LLMs enable flexible, high-quality topic extraction without training data.

### 4.1 Zero-Shot Classification

Zero-shot classification assigns documents to categories without fine-tuning:

```python
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

text = "The quarterly revenue increased by 15% compared to last year."
labels = ["finance", "technology", "legal", "marketing", "hr"]

result = classifier(text, labels)
# {'labels': ['finance', 'technology', ...], 'scores': [0.89, 0.05, ...]}
```

**Benefits for RAG:**
- No training data required
- Tag vocabulary can evolve without retraining
- Multi-label classification supported

### 2025 Model Benchmarks

**Zero-shot classification performance (February 2025):**

| Model | F1 Score | Speed | Best For |
|-------|----------|-------|----------|
| **Claude 3.5 Sonnet** | **0.7617** | ~1.8s/pred | Highest accuracy |
| DeepSeek-V3 | 0.7368 | - | Cost-effective alternative |
| GPT-4o | 0.7358 | 0.89s | Balanced speed/quality |
| GPT-4o-mini | 0.6933 | **0.86s** | Low-latency applications |
| Claude 3.5 Haiku | - | ~1.8s | Budget option |

**Source:** [E-commerce Classification Study](https://www.sciencedirect.com/science/article/pii/S2949719125000184), [Consumer Complaints Study](https://www.preprints.org/manuscript/202502.0720)

**Key Finding:** Fine-tuned smaller models consistently outperform zero-shot larger models when training data is available.

### 4.2 LLM4Tag: Production Architecture

LLM4Tag (February 2025) is an industrial-scale automatic tagging system deployed for "hundreds of millions of users":

**Architecture:**
1. **Graph-based tag recall:** Constructs highly relevant candidate tag sets
2. **Knowledge-enhanced generation:** Injects long-term and short-term knowledge
3. **Tag confidence calibration:** Generates reliable confidence scores

**Key innovation:** Uses knowledge graphs to constrain tag generation, reducing hallucinations.

**Source:** [LLM4Tag Paper](https://arxiv.org/html/2502.13481v2)

### 4.3 TopicGPT: Interactive Topic Modelling

TopicGPT integrates GPT-3.5/4 directly into topic modelling:

```python
from topicgpt import TopicGPT

# Create model
model = TopicGPT(api_key="your-key")

# Fit to documents
model.fit(documents)

# Get topics with natural language descriptions
topics = model.get_topics()
# [
#     {"id": 0, "label": "Climate Change Policy", "keywords": [...], "description": "..."},
#     {"id": 1, "label": "Renewable Energy", "keywords": [...], "description": "..."},
# ]

# Modify topics via natural language
model.merge_topics("Climate Change Policy", "Environmental Regulation")
model.split_topic("Technology", into=["AI/ML", "Cloud Computing", "Mobile"])
```

**Benefits:**
- Rich, human-readable topic descriptions
- Interactive refinement via text commands
- Explainable topic assignments

**Source:** [TopicGPT GitHub](https://github.com/ArikReuter/TopicGPT)

### 4.4 Hybrid: LDA + LLM

Combining traditional LDA with LLM labelling optimises cost and quality:

```python
from gensim.models import LdaModel
import openai

# Step 1: Run LDA to discover topic clusters
lda_model = LdaModel(corpus, num_topics=10)
topic_words = lda_model.show_topics(formatted=False)

# Step 2: Use LLM to generate human-readable labels (ONE API call)
prompt = f"""
Given these topic word distributions from topic modelling:
{topic_words}

Generate a short, descriptive label for each topic.
"""

response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)
```

**Cost comparison:**
| Approach | API Calls | Time | Cost (10K docs) |
|----------|-----------|------|-----------------|
| Pure LLM | 10,000 | ~3 hours | ~$10-50 |
| LDA + LLM labels | 1 | ~5 min | ~$0.01 |

**Source:** [Towards Data Science: LDA + LLM](https://towardsdatascience.com/document-topic-extraction-with-large-language-models-llm-and-the-latent-dirichlet-allocation-e4697e4dae87/)

### 4.5 Local-Only Options (Ollama)

ragd's privacy-first approach requires local alternatives:

```python
import ollama

def classify_document(text: str, labels: list[str]) -> dict:
    """Zero-shot classification using local Ollama."""
    prompt = f"""Classify this text into one of these categories: {labels}

Text: {text}

Return only the category name, nothing else."""

    response = ollama.generate(model="llama3.2", prompt=prompt)
    return response["response"].strip()
```

**Recommended local models:**
- **llama3.2:3b** - Fast, good quality
- **mistral:7b** - Best balance
- **phi-3:mini** - Smallest, fastest

---

## 5. Taxonomy & Hierarchy Generation

Building topic hierarchies enables drill-down navigation and structured knowledge organisation.

### 5.1 Taxonomy-Driven Knowledge Graph Construction (ACL 2025)

Pan et al. presented a framework combining taxonomies, LLMs, and RAG:

**Key findings:**
- Anchoring extraction to verified taxonomies **reduces hallucinations by 23.3%**
- RAG-based validation **improves F1 scores by 13.9%**
- Taxonomy constraints during LLM prompting enforce consistency

**Architecture:**
```
Seed Taxonomy → LLM Extraction (constrained) → RAG Validation → Refined Taxonomy
```

**Source:** [ACL 2025: Taxonomy-Driven KG Construction](https://aclanthology.org/2025.findings-acl.223/)

### 5.2 TaxoAlign: Scholarly Taxonomy Generation

TaxoAlign (October 2025) presents a three-stage LLM pipeline:

1. **Knowledge Slice Creation:** Extract domain concepts from documents
2. **Taxonomy Verbalisation:** LLM generates hierarchical relationships
3. **Taxonomy Refinement:** Iterative improvement based on metrics

**Evaluation metrics:**
- **Average degree score:** Measures structural similarity
- **Level-order traversal comparison:** Measures semantic similarity

**Source:** [TaxoAlign](https://arxiv.org/html/2510.17263)

### 5.3 LLM-Based Taxonomy Generation

```python
def generate_taxonomy(topics: list[str], llm_client) -> dict:
    """Generate topic hierarchy using LLM."""
    prompt = f"""
Given these topics extracted from a document corpus:
{topics}

Create a hierarchical taxonomy with:
1. Top-level categories (3-5)
2. Sub-categories under each
3. Leaf topics

Return as JSON:
{{
  "taxonomy": [
    {{
      "name": "Category Name",
      "children": [
        {{"name": "Subcategory", "children": [...]}}
      ]
    }}
  ]
}}
"""
    response = llm_client.generate(prompt)
    return json.loads(response)
```

### 5.4 Integration with ragd Knowledge Graph (F-022)

ragd's existing knowledge graph can store topic hierarchies:

```python
# Extend existing KnowledgeGraph schema
class TopicNode:
    name: str
    type: str = "TOPIC"
    parent: str | None = None
    level: int  # 0 = root, 1 = category, 2 = subcategory, etc.
    doc_count: int = 0

# Store in existing entity table with type="TOPIC"
# Use relationships table for parent-child links
```

---

## 6. Hybrid Architecture (Recommended)

For production RAG systems, a tiered approach optimises cost, quality, and latency.

### Recommended Pipeline

```
                    ┌─────────────────────────────────────────┐
                    │         Corpus-Level (Batch)            │
                    │  BERTopic → Discover themes             │
                    │  Run: On index rebuild, weekly          │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │       Document-Level (On Ingest)        │
                    │  KeyBERT → Extract keywords/tags        │
                    │  Run: Per document, during indexing     │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │        Enhancement (Optional)           │
                    │  LLM → Generate readable labels         │
                    │  Run: Batch, user-triggered             │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │       Taxonomy (User-Triggered)         │
                    │  LLM → Build/refine hierarchy           │
                    │  Run: On demand, after topic discovery  │
                    └─────────────────────────────────────────┘
```

### Cost/Quality Trade-offs

| Tier | Cost | Quality | Latency | Local? |
|------|------|---------|---------|--------|
| BERTopic | Low (compute) | High (clustering) | Batch | ✅ |
| KeyBERT | Low (compute) | Medium (keywords) | Real-time | ✅ |
| LLM Labels | Medium (API/$) | High (readable) | Seconds | ⚠️ Ollama |
| Taxonomy Gen | Higher (API/$) | High (structure) | Minutes | ⚠️ Ollama |

### Batch vs Real-Time Processing

| Operation | Mode | Trigger |
|-----------|------|---------|
| Topic discovery (BERTopic) | Batch | Index rebuild, scheduled |
| Document tagging (KeyBERT) | Real-time | Document ingestion |
| Topic labelling (LLM) | Batch | User command |
| Taxonomy generation | On-demand | User command |

---

## 7. RAG-Specific Considerations

### Metadata Enrichment Best Practices

From [RAG Best Practices Study](https://arxiv.org/abs/2407.01219):

1. **Tag during ingestion:** Enrich metadata at index time, not query time
2. **Hierarchical structure:** Organise as `topic → sub-topic → keyword`
3. **Consistent vocabulary:** Use controlled tag library (ragd F-062)
4. **Confidence scores:** Store extraction confidence for filtering

### Hierarchical Topic Structure for Retrieval

```yaml
# Recommended metadata structure
document:
  id: "doc-123"
  topics:
    - name: "Machine Learning"
      level: "category"
      confidence: 0.95
      children:
        - name: "Neural Networks"
          level: "subcategory"
          confidence: 0.87
  keywords:
    - name: "deep learning"
      score: 0.89
    - name: "transformer"
      score: 0.82
```

**Benefits:**
- Filter by broad category OR specific topic
- Hierarchical faceted search in WebUI
- Improves retrieval precision

### Query Classification Integration

Not all queries need topic-based retrieval:

```python
def classify_query(query: str) -> str:
    """Determine if query benefits from topic filtering."""
    # Factual queries: direct semantic search
    # Exploratory queries: topic-guided retrieval
    # Specific queries: keyword + semantic hybrid
    ...
```

### Chunk-Level vs Document-Level Topics

| Level | Use Case | Storage |
|-------|----------|---------|
| **Document** | Navigation, collections | Document metadata |
| **Chunk** | Fine-grained retrieval | Chunk metadata |

**Recommendation:** Store topics at document level, propagate to chunks for filtering.

---

## 8. Implementation Recommendations for ragd

### Phase 1: Enhance KeyBERT Integration (v0.4+)

**Current state:** KeyBERT available in `MetadataExtractor` (optional)

**Enhancements:**
- [ ] Configurable n-gram range via `ragd.yaml`
- [ ] Domain vocabulary seeding
- [ ] Store keywords as `TagEntry` with `source="auto-keybert"`
- [ ] CLI command: `ragd metadata keywords <doc-id>`

### Phase 2: Add BERTopic for Corpus Analysis (v0.5+)

**New feature:** Corpus-wide topic discovery

```bash
# Discover topics across all documents
ragd topics discover --num-topics auto

# View topic summary
ragd topics list

# Show documents in topic
ragd topics show "Machine Learning"

# Export topic model
ragd topics export topics.json
```

**Implementation:**
- New module: `src/ragd/topics/bertopic.py`
- Reuse existing embeddings from ChromaDB
- Store topics in SQLite (similar to knowledge graph)

### Phase 3: LLM Topic Labelling (v0.6+, Optional)

**Dependency:** Requires Ollama or cloud LLM

```bash
# Generate human-readable labels for discovered topics
ragd topics label --model ollama/llama3.2

# Update specific topic label
ragd topics rename "Topic 0" "Climate Change Policy"
```

### Phase 4: Taxonomy Builder (v1.0+)

**Feature:** Build and manage topic hierarchies

```bash
# Generate taxonomy from discovered topics
ragd topics taxonomy generate --output taxonomy.json

# Import existing taxonomy
ragd topics taxonomy import taxonomy.json

# Interactive refinement
ragd topics taxonomy edit
```

### Proposed pyproject.toml Changes

```toml
[project.optional-dependencies]
# Add to existing 'metadata' group or create new 'topics' group
topics = [
    "bertopic>=0.16.0",
    "umap-learn>=0.5.0",
    "hdbscan>=0.8.0",
]
```

---

## 9. Python Libraries & Dependencies

### Core Libraries

| Library | Purpose | Version | Notes |
|---------|---------|---------|-------|
| `bertopic` | Topic modelling | ≥0.16.0 | Includes BERTopic + integrations |
| `keybert` | Keyword extraction | ≥0.8.0 | Already in ragd |
| `sentence-transformers` | Embeddings | ≥2.2.0 | Already in ragd |
| `umap-learn` | Dimensionality reduction | ≥0.5.0 | Required by BERTopic |
| `hdbscan` | Clustering | ≥0.8.0 | Required by BERTopic |

### Optional Libraries

| Library | Purpose | When to Use |
|---------|---------|-------------|
| `transformers` | Zero-shot classification | BART/MNLI models |
| `scikit-llm` | Scikit-learn + LLM | Integration with sklearn pipelines |
| `topicgpt` | Interactive topic modelling | Research/experimentation |

### Memory Requirements

| Configuration | RAM | GPU VRAM |
|---------------|-----|----------|
| KeyBERT only | ~500MB | Optional |
| BERTopic (10K docs) | ~2GB | Optional |
| BERTopic (100K docs) | ~8GB | Recommended |
| BERTopic + LLM | ~4GB+ | Optional |

---

## 10. References

### Academic Papers (2024-2025)

- Ma et al. (2025). "AI-powered topic modeling: comparing LDA and BERTopic." *Experimental Biology and Medicine.* [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11906279/)
- Pan et al. (2025). "Taxonomy-Driven Knowledge Graph Construction for Domain-Specific Scientific Applications." *ACL Findings.* [Paper](https://aclanthology.org/2025.findings-acl.223/)
- "TaxoAlign: Scholarly Taxonomy Generation Using Language Models." *arXiv 2025.* [Paper](https://arxiv.org/html/2510.17263)
- "LLM4Tag: Automatic Tagging System for Information Retrieval via Large Language Models." *arXiv 2025.* [Paper](https://arxiv.org/html/2502.13481v2)
- Chae & Davidson (2025). "Large Language Models for Text Classification: From Zero-Shot Learning to Instruction-Tuning." *Sociological Methods & Research.* [Paper](https://journals.sagepub.com/doi/10.1177/00491241251325243)

### Benchmark Studies

- "LLMs for product classification in e-commerce: A zero-shot comparative study." *ScienceDirect 2025.* [Paper](https://www.sciencedirect.com/science/article/pii/S2949719125000184)
- "DeepSeek and GPT Fall Behind: Claude Leads in Zero-Shot Consumer Complaints Classification." *Preprints 2025.* [Paper](https://www.preprints.org/manuscript/202502.0720)
- "Experimental Comparison of Three Topic Modeling Methods." *Springer 2024.* [Paper](https://link.springer.com/chapter/10.1007/978-981-99-9109-9_37)

### Library Documentation

- [BERTopic Documentation](https://maartengr.github.io/BERTopic/)
- [BERTopic LLM Integration](https://maartengr.github.io/BERTopic/getting_started/representation/llm.html)
- [KeyBERT Documentation](https://maartengr.github.io/KeyBERT/)
- [TopicGPT GitHub](https://github.com/ArikReuter/TopicGPT)
- [Hugging Face Zero-Shot Classification](https://huggingface.co/tasks/zero-shot-classification)

### RAG Best Practices

- "Searching for Best Practices in Retrieval-Augmented Generation." *arXiv 2024.* [Paper](https://arxiv.org/abs/2407.01219)
- "Enhancing Retrieval-Augmented Generation: A Study of Best Practices." *arXiv 2025.* [Paper](https://arxiv.org/abs/2501.07391)

---

## Related Documentation

- [State-of-the-Art Tagging](./state-of-the-art-tagging.md) - Manual tagging, tag libraries, provenance, smart collections
- [State-of-the-Art Knowledge Graphs](./state-of-the-art-knowledge-graphs.md) - Entity extraction, GraphRAG
- [NLP Library Integration](./nlp-library-integration.md) - KeyBERT, spaCy integration patterns
- [F-022: Knowledge Graph Integration](../features/completed/F-022-knowledge-graph.md) - Entity extraction feature
- [F-030: Metadata Extraction](../features/completed/F-030-metadata-extraction.md) - KeyBERT integration
- [F-056: Specialised Task Models](../features/planned/F-056-specialised-task-models.md) - SLIM model classification

---

**Status**: Research complete
