# Research: State of the Art for Creating Collections in RAG Systems

## Executive Summary

This document reviews the current state of the art for creating collections of sources in RAG systems, distinguishing between manual, automatic, and hybrid approaches. The research covers tagging mechanisms, smart collections, knowledge graphs, and emerging LLM-based techniques.

---

## 1. Manual Collection Approaches

### 1.1 Traditional Folder-Based Organisation

**Static folders/directories** remain the simplest approach:
- Users manually move documents into folders
- Simple mental model but inflexible
- Documents can only exist in one location

### 1.2 Tag-Based Manual Organisation

**Manual tagging** provides more flexibility:
- Users assign one or more tags to documents
- Documents can belong to multiple "collections" via shared tags
- Requires user discipline and consistent vocabulary

**Best practices from research:**
- Use controlled vocabularies (taxonomies) to prevent tag sprawl
- Limit hierarchy to 3-4 levels maximum ([MatrixFlows](https://www.matrixflows.com/blog/10-best-practices-for-creating-taxonomy-for-your-company-knowledge-base))
- Implement faceted filtering alongside hierarchical navigation

### 1.3 Smart Folders / Saved Searches

**Virtual collections based on saved queries** - a mature pattern from desktop OSes:

| Platform | Implementation | First Released |
|----------|----------------|----------------|
| macOS | Smart Folders (Spotlight) | 2005 |
| Windows | Saved Searches (Windows Search) | 2006 |
| Gmail | Labels | 2004 |

**Key characteristics** ([Wikipedia](https://en.wikipedia.org/wiki/Virtual_folder), [ResearchSolutions](https://www.researchsolutions.com/blog/smart-folders-powering-research-workflows-with-continuous-saved-searches)):
- Documents don't physically move
- Collections auto-update as new matching documents appear
- Support complex boolean queries
- Same document can appear in multiple collections

**ragd's current implementation:**
- `CollectionManager` with `TagQuery` (include_all, include_any, exclude)
- Wildcard support (`project/*` matches `project/alpha`)
- Nested collections via parent_id

---

## 2. Automatic Collection Approaches

### 2.1 Document Clustering

**Unsupervised grouping by similarity** ([Wikipedia](https://en.wikipedia.org/wiki/Document_clustering), [arXiv](https://arxiv.org/pdf/2105.01004)):

**Techniques:**
- **HDBSCAN + UMAP**: State-of-the-art for dimensionality reduction + clustering
- **LDA (Latent Dirichlet Allocation)**: Topic modeling
- **BERTopic**: Combines BERT embeddings with clustering

**Strengths:**
- No manual effort required
- Discovers hidden themes in unlabelled data
- Useful for initial exploration

**Weaknesses:**
- Clusters may not align with user intent
- Requires tuning (number of clusters, similarity thresholds)
- Labels often require human interpretation

### 2.2 Automatic Tagging with ML/LLMs

#### 2.2.1 Pre-LLM Methods
- **TF-IDF + classification**: Simple but limited semantic understanding
- **KeyBERT**: Keyword extraction using BERT embeddings
- **Named Entity Recognition (NER)**: Extract entities as tags

#### 2.2.2 LLM-Based Tagging (2024-2025)

**LLM4Tag** ([arXiv](https://arxiv.org/html/2502.13481v2)) - deployed at scale:
1. Graph-based tag recall (candidate set generation)
2. Knowledge-enhanced tag generation (long/short-term knowledge injection)
3. Tag confidence calibration (reliable scores)

**Key advantages over traditional methods:**
- Better semantic understanding
- Can handle complex, nuanced content
- Adapts to evolving content without retraining

**BERTopic + LLMs** ([BERTopic docs](https://maartengr.github.io/BERTopic/getting_started/representation/llm.html)):
- Use LLMs to generate human-readable topic labels
- Combines clustering with generative labelling

**ragd's current implementation:**
- `SuggestionEngine` with sources: keybert, llm, ner, imported
- `TagEntry` with confidence scores and provenance tracking

### 2.3 Hierarchical/Taxonomy-Based Auto-Organisation

**Automatic taxonomy placement** ([arXiv SemEval-2025](https://arxiv.org/html/2504.07199v3)):
- LLMs classify documents into predefined taxonomy nodes
- Supports hierarchical subject headings (like library classification)

**ragd's current implementation:**
- `TagLibrary` with namespaces (document-type, sensitivity, status)
- Open vs closed namespaces for controlled vocabulary

---

## 3. Knowledge Graph Approaches

### 3.1 GraphRAG Architecture

**Microsoft GraphRAG** ([Microsoft](https://microsoft.github.io/graphrag/)):
1. Extract entities and relationships from text
2. Build community hierarchies
3. Generate summaries for communities
4. Use graph structure for retrieval

**Benefits:**
- Captures relationships between documents
- Enables multi-hop reasoning
- Discovers implicit connections

### 3.2 KG²RAG (Knowledge Graph-Guided RAG)

**Recent research** ([arXiv](https://arxiv.org/abs/2502.06864)):
- Uses knowledge graphs to provide fact-level relationships between chunks
- Improves diversity and coherence of retrieval
- Addresses chunking's disruption of document continuity

### 3.3 Automatic Linking

**Document GraphRAG** ([MDPI](https://www.mdpi.com/2079-9292/14/11/2102)):
- Graph-based document structuring
- Keyword-based semantic linking mechanism
- Preserves document intrinsic structure

**Key insight:** Graph RAG can highlight relationships between entities even if they don't co-occur in the same document ([OneReach](https://onereach.ai/blog/graph-rag-the-future-of-knowledge-management-software/)).

---

## 4. Hybrid Approaches (Emerging Best Practice)

### 4.1 Vector + Graph Hybrid

**Combining strengths** ([Neo4j](https://neo4j.com/blog/developer/rag-tutorial/), [DataCamp](https://www.datacamp.com/tutorial/knowledge-graph-rag)):
- Vector search for semantic similarity
- Knowledge graph for structured relationships
- Better context understanding and explainability

### 4.2 Auto-Suggest + Human Curation

**Workflow:**
1. System auto-generates tag suggestions (LLM, KeyBERT, NER)
2. Tags enter "pending" state with confidence scores
3. User reviews and confirms/rejects
4. Confirmed tags become part of controlled vocabulary

**ragd's current implementation:**
- `SuggestionEngine` generates pending suggestions
- `TagLibrary.promote_pending_tag()` for curation
- Full provenance tracking (source, confidence, created_by)

### 4.3 Hierarchical RAG

**Multi-level retrieval** ([MLJourney](https://mljourney.com/hierarchical-rag-architecture-for-large-document-collections-scaling-information-retrieval-for-enterprise-applications/)):
- Document level (metadata, summaries)
- Section level (chapters, major sections)
- Chunk level (text chunks for generation)

**Benefits:**
- Scales to large document collections
- Preserves document structure
- More efficient retrieval

---

## 5. State of ragd vs State of the Art

| Capability | State of the Art | ragd Current |
|------------|------------------|--------------|
| Manual tagging | Controlled vocabularies | TagLibrary with namespaces |
| Smart collections | Boolean queries, auto-update | CollectionManager with TagQuery |
| Auto-tagging | LLM4Tag, BERTopic | SuggestionEngine (KeyBERT, LLM, NER) |
| Tag provenance | Full audit trail | TagEntry with source, confidence, created_by |
| Document clustering | HDBSCAN + UMAP | Not implemented |
| Knowledge graphs | GraphRAG, KG²RAG | Not implemented |
| Hierarchical retrieval | Multi-level indexing | Partial (document/chunk) |

### 5.1 ragd Strengths
- **Excellent tag provenance** - best-in-class tracking of how tags were created
- **Smart collections** - mature implementation with boolean logic and wildcards
- **Controlled vocabulary** - TagLibrary with open/closed namespaces
- **Hybrid auto-suggest + curation** - suggestions with human review workflow

### 5.2 Gaps vs State of the Art
1. **No automatic clustering** - can't auto-discover collections from unlabelled docs
2. **No knowledge graph** - relationships between documents not explicitly modelled
3. **No GraphRAG** - no entity/relationship extraction for retrieval
4. **Limited hierarchy** - only document→chunk, not document→section→chunk

---

## 6. Recommendations for Future Development

### 6.1 Near-term (Low Complexity)
- **Auto-collection suggestions**: Analyse existing tags to suggest new smart collections
- **Tag co-occurrence analysis**: Show related tags to help users build collections

### 6.2 Medium-term
- **Document clustering**: Add HDBSCAN/UMAP clustering for collection discovery
- **Improved hierarchical chunking**: Section-level indexing for long documents

### 6.3 Long-term (High Complexity)
- **Knowledge graph layer**: Entity/relationship extraction and storage
- **GraphRAG integration**: Use graph structure to improve retrieval
- **Dynamic tag suggestions**: Real-time suggestions based on query context

---

## Sources

### RAG State of the Art
- [Prompt Engineering Guide - RAG](https://www.promptingguide.ai/research/rag)
- [arXiv - Systematic Review of RAG Systems](https://arxiv.org/html/2507.18910v1)
- [Aya Data - State of RAG 2025](https://www.ayadata.ai/the-state-of-retrieval-augmented-generation-rag-in-2025-and-beyond/)

### Automatic Tagging
- [arXiv - LLM4Tag](https://arxiv.org/html/2502.13481v2)
- [arXiv - LLM Topic Labelling](https://arxiv.org/html/2502.18469v1)
- [BERTopic - LLM Integration](https://maartengr.github.io/BERTopic/getting_started/representation/llm.html)
- [arXiv - SemEval-2025 Subject Tagging](https://arxiv.org/html/2504.07199v3)

### Document Clustering
- [arXiv - Automatic Collection Creation](https://arxiv.org/pdf/2105.01004)
- [Wikipedia - Document Clustering](https://en.wikipedia.org/wiki/Document_clustering)

### Knowledge Graphs
- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)
- [arXiv - KG²RAG](https://arxiv.org/abs/2502.06864)
- [Neo4j - RAG Tutorial](https://neo4j.com/blog/developer/rag-tutorial/)
- [MLJourney - Hierarchical RAG](https://mljourney.com/hierarchical-rag-architecture-for-large-document-collections-scaling-information-retrieval-for-enterprise-applications/)

### Smart Folders
- [Wikipedia - Virtual Folder](https://en.wikipedia.org/wiki/Virtual_folder)
- [ResearchSolutions - Smart Folders](https://www.researchsolutions.com/blog/smart-folders-powering-research-workflows-with-continuous-saved-searches)

### Taxonomy Design
- [MatrixFlows - Knowledge Base Taxonomy](https://www.matrixflows.com/blog/10-best-practices-for-creating-taxonomy-for-your-company-knowledge-base)
- [Innovatia - Information Architecture for RAG](https://www.innovatia.net/blog/the-four-critical-components-of-information-architecture-for-rag)

---

## 7. Deep Dive: Document Clustering (HDBSCAN + UMAP + BERTopic)

### 7.1 Why HDBSCAN + UMAP?

HDBSCAN struggles with high-dimensional data because it cannot define density effectively in high dimensions. UMAP preprocessing can improve clustering results by up to 60% in accuracy ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7340901/)).

### 7.2 Recommended Parameters

**UMAP Configuration for Clustering** ([UMAP docs](https://umap-learn.readthedocs.io/en/latest/clustering.html)):
```python
import umap

reducer = umap.UMAP(
    n_neighbors=15,      # Lower = more local structure
    n_components=5,      # Target dimensions (not 2 for clustering)
    min_dist=0.0,        # CRITICAL: Set to 0 for clustering
    metric='cosine',     # Good for text embeddings
    random_state=42      # Reproducibility
)
```

**HDBSCAN Configuration**:
```python
import hdbscan

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=10,   # Minimum points per cluster
    min_samples=5,         # Core point threshold
    cluster_selection_epsilon=0.0,
    prediction_data=True   # For soft clustering
)
```

### 7.3 Advanced: UMAP → t-SNE → HDBSCAN

For reduced noise, apply UMAP to 10 dimensions, then t-SNE to 2 dimensions before HDBSCAN. This reduces noise from 41% to 17% ([GDELT](https://blog.gdeltproject.org/visualizing-an-entire-day-of-global-news-coverage-how-umap-t-sne-reduces-hdbscan-clustering-noise/)).

### 7.4 BERTopic Pipeline

**Default pipeline** ([BERTopic](https://maartengr.github.io/BERTopic/index.html)):
1. **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)
2. **Dimensionality reduction**: UMAP
3. **Clustering**: HDBSCAN
4. **Topic representation**: c-TF-IDF

**Basic usage**:
```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

# Custom embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Create topic model
topic_model = BERTopic(
    embedding_model=embedding_model,
    min_topic_size=10,
    nr_topics="auto"  # Auto-discover number of topics
)

# Fit and transform
topics, probs = topic_model.fit_transform(documents)
```

**LLM-enhanced labelling**:
```python
from bertopic.representation import OpenAI

# Use GPT for topic labels
representation_model = OpenAI(model="gpt-4o-mini")
topic_model = BERTopic(representation_model=representation_model)
```

### 7.5 Integration with RAG Collections

**Workflow for auto-collection discovery**:
1. Embed all documents using sentence-transformers
2. Apply UMAP dimensionality reduction
3. Cluster with HDBSCAN
4. Use BERTopic/LLM to generate cluster labels
5. Create smart collections from clusters
6. Present to user for curation

**Key decisions**:
- Handle outliers (HDBSCAN label -1) - don't force into collections
- Allow documents to belong to multiple clusters (soft clustering)
- Track cluster provenance (`source: auto-clustering`)

---

## 8. Deep Dive: GraphRAG and Knowledge Graphs

### 8.1 Microsoft GraphRAG Architecture

**Four primary layers** ([Microsoft](https://microsoft.github.io/graphrag/), [RAGAboutIt](https://ragaboutit.com/how-to-build-production-ready-graphrag-systems-with-microsofts-latest-framework-a-complete-enterprise-implementation-guide/)):

1. **Ingestion Layer**: Process and chunk documents into TextUnits
2. **Graph Construction Layer**: Extract entities and relationships
3. **Community Detection**: Build hierarchical community structure
4. **Retrieval Layer**: Navigate knowledge graph for queries

### 8.2 Entity Extraction

**Extraction prompt structure**:
1. Extraction instructions
2. Few-shot examples
3. Real data (document chunks)
4. Gleanings (multi-turn refinement)

**Auto-tuning** ([Microsoft Research](https://www.microsoft.com/en-us/research/blog/graphrag-auto-tuning-provides-rapid-adaptation-to-new-domains/)):
- Automatically generates domain-specific prompts
- Creates appropriate persona for extraction
- Adapts to industry terminology

### 8.3 Community Hierarchies

**Why communities matter**:
- Enable sense-making at scale
- Organise graph into semantically meaningful subgraphs
- Reduce query times
- Support multi-level hierarchies (communities → sub-communities)

### 8.4 Search Strategies

| Strategy | Use Case | How It Works |
|----------|----------|--------------|
| **Local Search** | Specific entities, precise details | Combines KG facts + text chunks |
| **Global Search** | Broad understanding | Map-reduce over community reports |
| **DRIFT Search** | Entity reasoning with context | Fan-out to neighbours + community info |

### 8.5 Implementation with Neo4j + LangChain

**Installation**:
```bash
pip install langchain langchain-neo4j neo4j sentence-transformers
```

**Basic setup** ([Neo4j](https://neo4j.com/blog/developer/rag-tutorial/)):
```python
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI

# Connect to Neo4j
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="your-password"
)

# Query chain
chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0),
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True
)

# Query
result = chain.run("What documents mention Project X?")
```

**Knowledge graph construction from documents**:
```python
from langchain_neo4j import LLMGraphTransformer
from langchain_openai import ChatOpenAI

# Extract graph from documents
llm = ChatOpenAI(model="gpt-4o")
transformer = LLMGraphTransformer(llm=llm)

# Convert documents to graph
graph_documents = transformer.convert_to_graph_documents(documents)

# Import to Neo4j
graph.add_graph_documents(
    graph_documents,
    baseEntityLabel=True  # Adds __Entity__ label for indexing
)
```

---

## 9. Deep Dive: LLM-Based Auto-Tagging

### 9.1 LLM4Tag Architecture

**Three modules** ([arXiv](https://arxiv.org/html/2502.13481v2)):

1. **Graph-based Tag Recall**
   - Builds content-tag graph dynamically
   - Retrieves highly relevant candidate tags
   - Reduces search space from millions to dozens

2. **Knowledge-enhanced Tag Generation**
   - Long-term knowledge: Domain expertise
   - Short-term knowledge: Recent/emerging content
   - Continual knowledge evolution without retraining

3. **Tag Confidence Calibration**
   - Reduces hallucination
   - Consistent relevance metric
   - Enables threshold-based filtering

### 9.2 Confidence Thresholds

**Best practices** ([AWS SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-automated-labeling.html), [arXiv](https://arxiv.org/abs/2211.12620)):

| Confidence | Action |
|------------|--------|
| > 0.9 | Auto-apply tag |
| 0.7-0.9 | Suggest for review |
| < 0.7 | Discard or flag |

**Trade-off**: Higher threshold = better accuracy, lower coverage

**Example workflow**:
```python
def process_tag_suggestion(tag, confidence):
    if confidence >= 0.9:
        return TagStatus.AUTO_APPLIED
    elif confidence >= 0.7:
        return TagStatus.PENDING_REVIEW
    else:
        return TagStatus.REJECTED
```

### 9.3 Tiered Human-AI Workflow

**Recommended pipeline**:
1. **Auto-tag** with LLM (KeyBERT, LLM4Tag)
2. **Route by confidence**:
   - High confidence → auto-apply with spot checks
   - Medium confidence → human review queue
   - Low confidence → discard
3. **Learn from corrections** to improve thresholds
4. **Promote to library** when patterns emerge

**Key metrics**:
- Coverage (% of documents tagged)
- Accuracy (correct tags / total tags)
- Human review rate (% requiring review)

---

## 10. Deep Dive: Hybrid Approaches

### 10.1 HybridRAG: Vector + Knowledge Graph

**Why combine both?** ([arXiv](https://arxiv.org/abs/2408.04948), [Memgraph](https://memgraph.com/blog/why-hybridrag)):

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| **VectorRAG** | Semantic similarity, handles vague queries | No relationship understanding |
| **GraphRAG** | Structured relationships, multi-hop reasoning | Requires schema, expensive to build |
| **HybridRAG** | Best of both | More complex architecture |

### 10.2 Implementation Pattern

**Three retrieval methods in one system**:
```python
class HybridRetriever:
    def __init__(self, vector_store, knowledge_graph):
        self.vector_store = vector_store
        self.kg = knowledge_graph

    def retrieve(self, query, method="hybrid"):
        if method == "vector":
            return self.vector_search(query)
        elif method == "graph":
            return self.graph_search(query)
        else:  # hybrid
            vector_results = self.vector_search(query)
            graph_results = self.graph_search(query)
            return self.fuse_results(vector_results, graph_results)

    def fuse_results(self, vector_results, graph_results):
        # Combine and rerank
        combined = vector_results + graph_results
        return self.rerank(combined)
```

### 10.3 Real-World Example: AlzKB

Cedars-Sinai's Alzheimer's Knowledge Base ([QED42](https://www.qed42.com/insights/how-knowledge-graphs-take-rag-beyond-retrieval)):
- **Graph DB**: Biomedical entities (genes, drugs, diseases)
- **Vector DB**: Semantic similarity searches
- **Result**: Identified FDA-approved drugs as treatment candidates

### 10.4 Agent-Based Selection

**Let the system choose retrieval method**:
```python
from langchain.agents import AgentExecutor

tools = [
    Tool(name="semantic_search", func=vector_retriever),
    Tool(name="graph_query", func=graph_retriever),
    Tool(name="hybrid_search", func=hybrid_retriever)
]

agent = AgentExecutor(
    agent=create_react_agent(llm, tools),
    tools=tools
)

# Agent decides which tool to use based on query
result = agent.run("What entities are related to Document X?")
```

---

## 11. Summary: Collection Creation Taxonomy

```
Collection Creation Methods
├── Manual
│   ├── Static folders (physical location)
│   ├── Manual tagging (user-assigned)
│   └── Smart folders (saved queries)
│
├── Automatic
│   ├── Clustering-based
│   │   ├── HDBSCAN + UMAP
│   │   ├── BERTopic
│   │   └── Top2Vec
│   │
│   ├── Tagging-based
│   │   ├── KeyBERT (keywords)
│   │   ├── NER (entities)
│   │   ├── LLM classification
│   │   └── LLM4Tag (production-scale)
│   │
│   └── Graph-based
│       ├── Entity extraction
│       ├── Relationship discovery
│       └── Community detection
│
└── Hybrid
    ├── Auto-suggest + human curation
    ├── Vector + knowledge graph (HybridRAG)
    └── Clustering → smart collection promotion
```

---

## Sources (Expanded)

### Document Clustering
- [UMAP Documentation - Clustering](https://umap-learn.readthedocs.io/en/latest/clustering.html)
- [PMC - UMAP Clustering Improvement](https://pmc.ncbi.nlm.nih.gov/articles/PMC7340901/)
- [Dylan Castillo - Clustering with OpenAI + HDBSCAN](https://dylancastillo.co/posts/clustering-documents-with-openai-langchain-hdbscan.html)
- [BERTopic Official Documentation](https://maartengr.github.io/BERTopic/index.html)
- [Pinecone - Advanced BERTopic](https://www.pinecone.io/learn/bertopic/)

### GraphRAG / Knowledge Graphs
- [Microsoft GraphRAG Documentation](https://microsoft.github.io/graphrag/)
- [Microsoft Research - GraphRAG Auto-Tuning](https://www.microsoft.com/en-us/research/blog/graphrag-auto-tuning-provides-rapid-adaptation-to-new-domains/)
- [Neo4j - RAG Tutorial](https://neo4j.com/blog/developer/rag-tutorial/)
- [LangChain - Neo4j Integration](https://neo4j.com/labs/genai-ecosystem/langchain/)
- [LangChain Blog - KG-enhanced RAG](https://blog.langchain.com/enhancing-rag-based-applications-accuracy-by-constructing-and-leveraging-knowledge-graphs/)

### LLM-Based Tagging
- [arXiv - LLM4Tag](https://arxiv.org/html/2502.13481v2)
- [Medium - Document Classification with LLM](https://medium.com/@andy.bosyi/document-classification-and-tagging-with-llm-and-ml-ea404599dcc6)
- [Vellum - Automatic Data Labeling](https://www.vellum.ai/blog/automatic-data-labeling-with-llms)
- [AWS SageMaker - Automated Labeling](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-automated-labeling.html)

### Hybrid Approaches
- [arXiv - HybridRAG](https://arxiv.org/abs/2408.04948)
- [Memgraph - Why HybridRAG](https://memgraph.com/blog/why-hybridrag)
- [Neo4j - Enhance RAG with KG](https://neo4j.com/blog/developer/enhance-rag-knowledge-graph/)
- [QED42 - KG Beyond Retrieval](https://www.qed42.com/insights/how-knowledge-graphs-take-rag-beyond-retrieval)

### Semantic Clustering for RAG
- [arXiv - Topic Embeddings for Retrieval](https://arxiv.org/html/2408.10435v1)
- [Medium - Context-Aware RAG](https://medium.com/@jsbeaudry/context-aware-retrieval-augmented-generation-rag-enhancing-retrieval-through-semantic-document-657bcb0675ff)
- [GreenNode - Best Embedding Models](https://greennode.ai/blog/best-embedding-models-for-rag)

---

## Related Documentation

- [State of the Art: Tagging](./state-of-the-art-tagging.md) - Detailed tagging research
- [State of the Art: Knowledge Graphs](./state-of-the-art-knowledge-graphs.md) - Graph database research
- [State of the Art: RAG](./state-of-the-art-rag.md) - General RAG landscape
