# State-of-the-Art Knowledge Graphs for RAG

> **Implementation Note:** This research informed the design of F-022 Knowledge Graph Integration. See [ADR-0031](../decisions/adrs/0031-knowledge-graph-storage.md) for the implementation decision to use SQLite instead of Kuzu, prioritising simplicity and dependency minimisation.

## Executive Summary

**Key Recommendations for ragd:**

1. **Graph Database:** Use Kuzu for local deployment - 18x faster ingestion than Neo4j, embedded architecture
2. **Entity Extraction:** GLiNER for flexible NER, spaCy for traditional entities, LLM for complex extraction
3. **Community Detection:** Leiden algorithm (not Louvain) - guaranteed well-connected communities
4. **Query Pattern:** Hybrid vector + graph retrieval with reranking for best results
5. **When to Use:** Multi-hop reasoning, entity-centric queries, corpus-wide understanding

---

## When GraphRAG is Worth the Complexity

### Traditional RAG Limitations

| Query Type | Vector RAG | GraphRAG |
|------------|------------|----------|
| "What is X?" | Excellent | Good |
| "Who is related to Y?" | Poor | Excellent |
| "What are the main themes?" | Poor | Excellent |
| "How does A connect to B?" | Very Poor | Excellent |
| "Summarise everything about topic Z" | Moderate | Excellent |

### Decision Matrix

```
Should you use GraphRAG?
│
├─ Do you need multi-hop reasoning?
│   └─ YES → GraphRAG beneficial
│
├─ Are entity relationships important?
│   └─ YES → GraphRAG beneficial
│
├─ Do you need corpus-wide summaries?
│   └─ YES → GraphRAG beneficial
│
├─ Is your data highly structured with known entities?
│   └─ YES → GraphRAG beneficial
│
├─ Simple factual lookup queries only?
│   └─ YES → Vector RAG sufficient
│
└─ Cost of complexity worth the benefit?
    ├─ Small corpus (<100 docs) → Probably not
    └─ Large corpus with relationships → Yes
```

**Source:** [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)

---

## Part 1: Microsoft GraphRAG Architecture

### Overview

GraphRAG combines text extraction, network analysis, and LLM summarisation into an end-to-end system for understanding text datasets.

### Pipeline Steps

```
Raw Documents
      │
      ▼
┌─────────────────────────────────────┐
│  1. Text Chunking                   │
│     Split into manageable units     │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  2. Entity & Relationship Extraction│
│     LLM identifies entities/relations│
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  3. Knowledge Graph Construction    │
│     Build graph from extractions    │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  4. Community Detection (Leiden)    │
│     Hierarchical clustering         │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  5. Community Summarisation         │
│     LLM generates summaries         │
└─────────────────────────────────────┘
      │
      ▼
Knowledge Graph + Community Summaries
```

### Query Modes

**Local Search:**
- Uses entity/relationship data
- Best for specific questions
- "What did Person X do in 2023?"

**Global Search:**
- Uses community summaries
- Best for broad questions
- "What are the main themes in this dataset?"

### Implementation Example

```python
import graphrag

# Build index
index = graphrag.build_index(
    documents=documents,
    llm_model="gpt-4",
    embedding_model="text-embedding-3-small"
)

# Local query (specific)
local_result = index.local_search(
    "What projects did Alice work on?"
)

# Global query (thematic)
global_result = index.global_search(
    "What are the main research themes?"
)
```

**Source:** [Microsoft GraphRAG GitHub](https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/)

---

## Part 2: Entity Extraction Techniques

### Comparison of NER Approaches

| Approach | Speed | Flexibility | Accuracy | Best For |
|----------|-------|-------------|----------|----------|
| **spaCy** | Fast | Limited types | High | Standard entities |
| **GLiNER** | Fast | Any type | High | Custom entities |
| **LLM-based** | Slow | Unlimited | Very High | Complex extraction |
| **Hybrid** | Medium | High | Very High | Production systems |

### spaCy for Standard NER

```python
import spacy

# Load model with NER
nlp = spacy.load("en_core_web_trf")

def extract_entities_spacy(text: str) -> list[dict]:
    """Extract standard entities using spaCy."""
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })

    return entities

# Standard entity types: PERSON, ORG, GPE, DATE, MONEY, etc.
```

### GLiNER for Custom Entities

GLiNER allows zero-shot extraction of any entity type without training:

```python
from gliner import GLiNER

# Load model
model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")

def extract_entities_gliner(
    text: str,
    entity_types: list[str]
) -> list[dict]:
    """Extract custom entity types using GLiNER."""

    # Define what to extract
    labels = entity_types  # e.g., ["technology", "concept", "metric"]

    # Extract entities
    entities = model.predict_entities(text, labels, threshold=0.5)

    return [
        {
            "text": e["text"],
            "label": e["label"],
            "score": e["score"],
            "start": e["start"],
            "end": e["end"]
        }
        for e in entities
    ]

# Example: Custom domain entities
entities = extract_entities_gliner(
    "The RAG system achieved 95% accuracy using ChromaDB.",
    ["technology", "metric", "database"]
)
# Returns: [{"text": "RAG system", "label": "technology"}, ...]
```

### LLM-Based Extraction

For complex scenarios requiring relationship extraction:

```python
from openai import OpenAI

EXTRACTION_PROMPT = """
Extract all entities and relationships from the following text.

Return a JSON object with:
- entities: list of {name, type, description}
- relationships: list of {source, target, type, description}

Text: {text}

JSON:
"""

async def extract_with_llm(text: str) -> dict:
    """Extract entities and relationships using LLM."""
    client = OpenAI()

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": EXTRACTION_PROMPT.format(text=text)}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
```

### Hybrid Pipeline (Recommended)

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class Entity:
    text: str
    type: str
    source: Literal["spacy", "gliner", "llm"]
    confidence: float

class HybridEntityExtractor:
    """Combine multiple extraction methods."""

    def __init__(self):
        self.spacy_nlp = spacy.load("en_core_web_trf")
        self.gliner = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")

    def extract(
        self,
        text: str,
        custom_types: list[str] | None = None,
        use_llm: bool = False
    ) -> list[Entity]:
        """Extract entities using hybrid approach."""
        entities = []

        # 1. spaCy for standard entities
        doc = self.spacy_nlp(text)
        for ent in doc.ents:
            entities.append(Entity(
                text=ent.text,
                type=ent.label_,
                source="spacy",
                confidence=0.9  # spaCy doesn't provide scores
            ))

        # 2. GLiNER for custom types
        if custom_types:
            gliner_entities = self.gliner.predict_entities(
                text, custom_types, threshold=0.5
            )
            for ent in gliner_entities:
                entities.append(Entity(
                    text=ent["text"],
                    type=ent["label"],
                    source="gliner",
                    confidence=ent["score"]
                ))

        # 3. Deduplicate and merge
        return self._deduplicate(entities)
```

**Source:** [DerwenAI/strwythura](https://github.com/DerwenAI/strwythura)

---

## Part 3: Graph Database Selection

### Comparison for Local RAG

| Database | Architecture | Speed | Cypher | Python API | Best For |
|----------|--------------|-------|--------|------------|----------|
| **Kuzu** | Embedded | Very Fast | Yes | Native | Local RAG |
| **Neo4j** | Server | Fast | Yes | Driver | Enterprise |
| **NetworkX** | In-memory | Slow | No | Native | Small graphs |
| **igraph** | In-memory | Fast | No | Native | Graph algorithms |

### Kuzu: The Embedded Choice

**Why Kuzu for ragd:**
- 18x faster ingestion than Neo4j
- Embedded (no server needed)
- Column-oriented storage
- Vectorised query execution
- Full Cypher support
- Apache 2.0 license

**Benchmark Results:**
- Ingestion: ~18x faster than Neo4j
- Multi-hop queries: Up to 188x faster
- Path finding: Significant speedup

```python
import kuzu

# Create database
db = kuzu.Database("./ragd_graph")
conn = kuzu.Connection(db)

# Define schema (required in Kuzu)
conn.execute("""
    CREATE NODE TABLE Entity (
        id STRING PRIMARY KEY,
        name STRING,
        type STRING,
        description STRING,
        embedding FLOAT[768]
    )
""")

conn.execute("""
    CREATE REL TABLE RELATES_TO (
        FROM Entity TO Entity,
        type STRING,
        description STRING,
        weight FLOAT
    )
""")

# Insert entities
conn.execute("""
    CREATE (e:Entity {
        id: $id,
        name: $name,
        type: $type,
        description: $description
    })
""", {"id": "e1", "name": "Alice", "type": "PERSON", "description": "..."})

# Query relationships
result = conn.execute("""
    MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
    WHERE a.name = 'Alice'
    RETURN a.name, r.type, b.name
""")
```

**Source:** [Kuzu Benchmark Study](https://github.com/prrao87/kuzudb-study)

### NetworkX for Prototyping

For small graphs or algorithm exploration:

```python
import networkx as nx

# Create graph
G = nx.DiGraph()

# Add entities
for entity in entities:
    G.add_node(entity.id, **entity.__dict__)

# Add relationships
for rel in relationships:
    G.add_edge(rel.source, rel.target, type=rel.type)

# Graph algorithms
communities = nx.community.louvain_communities(G)
centrality = nx.pagerank(G)
paths = nx.shortest_path(G, source="entity1", target="entity2")
```

---

## Part 4: Community Detection

### Leiden vs Louvain

| Aspect | Louvain | Leiden |
|--------|---------|--------|
| **Speed** | Fast | Faster |
| **Quality** | Good | Better |
| **Connectivity** | May disconnect | Guaranteed connected |
| **Iterations** | May not converge | Converges |
| **Recommendation** | Legacy | Use this |

### Why Leiden is Better

Research shows Louvain can produce:
- Up to 25% badly connected communities
- Up to 16% disconnected communities

Leiden addresses this by adding a refinement phase that guarantees well-connected communities.

### Implementation

```python
import leidenalg
import igraph as ig

def detect_communities(
    entities: list[dict],
    relationships: list[dict],
    resolution: float = 1.0
) -> list[list[str]]:
    """Detect communities using Leiden algorithm."""

    # Build igraph from data
    G = ig.Graph(directed=True)

    # Add vertices
    G.add_vertices(len(entities))
    for i, entity in enumerate(entities):
        G.vs[i]["name"] = entity["id"]
        G.vs[i]["type"] = entity["type"]

    # Add edges
    entity_id_to_idx = {e["id"]: i for i, e in enumerate(entities)}
    edges = [
        (entity_id_to_idx[r["source"]], entity_id_to_idx[r["target"]])
        for r in relationships
        if r["source"] in entity_id_to_idx and r["target"] in entity_id_to_idx
    ]
    G.add_edges(edges)

    # Run Leiden
    partition = leidenalg.find_partition(
        G,
        leidenalg.ModularityVertexPartition,
        resolution_parameter=resolution
    )

    # Extract communities
    communities = []
    for community in partition:
        entity_ids = [G.vs[idx]["name"] for idx in community]
        communities.append(entity_ids)

    return communities
```

### Hierarchical Communities

GraphRAG builds a hierarchy of communities for different query granularities:

```python
def build_community_hierarchy(
    G: ig.Graph,
    levels: int = 3
) -> dict[int, list[list[str]]]:
    """Build hierarchical community structure."""
    hierarchy = {}

    for level in range(levels):
        # Higher resolution = more, smaller communities
        resolution = 1.0 / (level + 1)

        partition = leidenalg.find_partition(
            G,
            leidenalg.ModularityVertexPartition,
            resolution_parameter=resolution
        )

        hierarchy[level] = [
            [G.vs[idx]["name"] for idx in community]
            for community in partition
        ]

    return hierarchy
```

**Source:** [Leiden Algorithm Paper](https://www.nature.com/articles/s41598-019-41695-z)

---

## Part 5: Hybrid Vector + Graph Retrieval

### Query Pattern Architecture

```
User Query
    │
    ├─────────────────────┬──────────────────────┐
    ▼                     ▼                      ▼
Vector Search      Entity Extraction      Graph Traversal
    │                     │                      │
    │                     ▼                      │
    │              Entity Linking                │
    │                     │                      │
    ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────┐
│                     Fusion                          │
│           Combine and deduplicate results           │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                   Reranking                         │
│        Cross-encoder or LLM-based scoring           │
└─────────────────────────────────────────────────────┘
    │
    ▼
Final Context for Generation
```

### LlamaIndex PropertyGraphIndex

```python
from llama_index.core import PropertyGraphIndex
from llama_index.graph_stores.kuzu import KuzuGraphStore
from llama_index.core.retrievers import (
    VectorContextRetriever,
    LLMSynonymRetriever,
    TextToCypherRetriever
)

# Create graph store
graph_store = KuzuGraphStore(db_path="./ragd_graph")

# Build index
index = PropertyGraphIndex.from_documents(
    documents,
    graph_store=graph_store,
    embed_model=embed_model,
    llm=llm
)

# Hybrid retriever combining multiple strategies
class HybridGraphRetriever:
    def __init__(self, index: PropertyGraphIndex):
        self.vector_retriever = VectorContextRetriever(
            index.property_graph_store,
            embed_model=embed_model,
            similarity_top_k=10
        )
        self.cypher_retriever = TextToCypherRetriever(
            index.property_graph_store,
            llm=llm
        )
        self.reranker = cross_encoder_reranker

    def retrieve(self, query: str) -> list[Node]:
        # Get results from both retrievers
        vector_nodes = self.vector_retriever.retrieve(query)
        cypher_nodes = self.cypher_retriever.retrieve(query)

        # Combine and rerank
        all_nodes = vector_nodes + cypher_nodes
        reranked = self.reranker.postprocess_nodes(
            all_nodes, query_str=query
        )

        return reranked[:10]
```

### Custom Graph Traversal

```python
def multi_hop_retrieval(
    query: str,
    start_entities: list[str],
    graph_store,
    max_hops: int = 2
) -> list[dict]:
    """Retrieve context via multi-hop graph traversal."""

    context = []
    visited = set()

    def traverse(entity_id: str, depth: int):
        if depth > max_hops or entity_id in visited:
            return
        visited.add(entity_id)

        # Get entity and its relationships
        entity = graph_store.get_entity(entity_id)
        context.append(entity)

        relationships = graph_store.get_relationships(entity_id)
        for rel in relationships:
            context.append(rel)
            traverse(rel["target"], depth + 1)

    # Start traversal from query-relevant entities
    for entity_id in start_entities:
        traverse(entity_id, 0)

    return context
```

**Source:** [LlamaIndex PropertyGraphIndex](https://www.llamaindex.ai/blog/introducing-the-property-graph-index-a-powerful-new-way-to-build-knowledge-graphs-with-llms)

---

## Recommended Architecture for ragd

### Knowledge Graph Configuration (v0.8+)

```yaml
# ~/.ragd/config.yaml

knowledge_graph:
  enabled: false  # Enable in v0.8

  # Graph database
  database:
    type: kuzu  # kuzu, neo4j, networkx
    path: "~/.ragd/graph_db"

  # Entity extraction
  extraction:
    # Hybrid extraction pipeline
    spacy_model: "en_core_web_trf"
    gliner_model: "urchade/gliner_multi-v2.1"
    custom_entity_types:
      - "technology"
      - "concept"
      - "method"
    use_llm_extraction: false  # Enable for complex docs

  # Community detection
  communities:
    algorithm: leiden  # leiden, louvain
    resolution: 1.0
    hierarchical: true
    levels: 3

  # Retrieval
  retrieval:
    strategy: hybrid  # vector, graph, hybrid
    vector_weight: 0.6
    graph_weight: 0.4
    max_hops: 2
    rerank: true
```

### Implementation Phases

```
Phase 1 (v0.8): Basic Graph Construction
├── Entity extraction (spaCy + GLiNER)
├── Kuzu graph storage
└── Simple graph queries

Phase 2 (v0.9): Community Summaries
├── Leiden community detection
├── LLM-generated summaries
└── Global search capability

Phase 3 (v1.0): Hybrid Retrieval
├── Vector + graph fusion
├── Multi-hop reasoning
└── Reranking integration
```

### Cost-Benefit Analysis

| Aspect | Vector RAG | GraphRAG | Hybrid |
|--------|------------|----------|--------|
| **Setup Complexity** | Low | High | High |
| **Query Latency** | Fast | Medium | Medium |
| **Storage Requirements** | Low | Medium | High |
| **Multi-hop Reasoning** | Poor | Excellent | Excellent |
| **Global Questions** | Poor | Excellent | Excellent |
| **Simple Lookup** | Excellent | Good | Excellent |
| **Maintenance** | Low | High | High |

**Recommendation:** Start with vector RAG (v0.1-v0.7), add graph capabilities when multi-hop reasoning is needed (v0.8+).

---

## References

### GraphRAG
- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)
- [GraphRAG Research Paper](https://arxiv.org/abs/2404.16130)
- [GraphRAG Auto-Tuning](https://www.microsoft.com/en-us/research/blog/graphrag-auto-tuning-provides-rapid-adaptation-to-new-domains/)

### Entity Extraction
- [GLiNER GitHub](https://github.com/urchade/GLiNER)
- [spaCy NER](https://spacy.io/usage/linguistic-features#named-entities)
- [DerwenAI/strwythura](https://github.com/DerwenAI/strwythura)

### Graph Databases
- [Kuzu Documentation](https://docs.kuzudb.com/)
- [Kuzu Benchmark Study](https://github.com/prrao87/kuzudb-study)
- [Neo4j GraphRAG Integration](https://neo4j.com/blog/developer/microsoft-graphrag-neo4j/)

### Community Detection
- [Leiden Algorithm Paper](https://www.nature.com/articles/s41598-019-41695-z)
- [NVIDIA GPU-Accelerated Leiden](https://developer.nvidia.com/blog/how-to-accelerate-community-detection-in-python-using-gpu-powered-leiden/)

### LlamaIndex Integration
- [PropertyGraphIndex](https://www.llamaindex.ai/blog/introducing-the-property-graph-index-a-powerful-new-way-to-build-knowledge-graphs-with-llms)
- [Knowledge Graph RAG Query Engine](https://docs.llamaindex.ai/en/stable/examples/query_engine/knowledge_graph_rag_query_engine/)

---

## Related Documentation

- [State-of-the-Art NER Indexing](./state-of-the-art-ner-indexing.md) - NER integration with indexing pipelines
- [State-of-the-Art NER](./state-of-the-art-ner.md) - Named entity recognition techniques
- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - GraphRAG section
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Entity embeddings
- [ADRs](../decisions/adrs/README.md) - Architecture decisions

---

**Status:** Research complete
