# F-022: Knowledge Graph Integration

## Overview

**Research**: [State-of-the-Art Knowledge Graphs](../../research/state-of-the-art-knowledge-graphs.md)
**Milestone**: v0.8
**Priority**: P2

## Problem Statement

Vector search finds semantically similar content but misses explicit relationships. A knowledge graph captures entities and their relationships, enabling queries like "what topics are related to authentication?" and revealing connections users might miss.

## Design Approach

### Architecture

```
Indexed Documents
    ↓
Entity Extraction (NER)
    ↓
Relationship Detection
    ↓
Knowledge Graph (Kuzu)
    ↓
Graph-Enhanced Retrieval
```

### Technologies

- **Kuzu**: Embedded graph database (SQLite for graphs)
- **spaCy**: Entity extraction (NER)
- **Local LLM**: Relationship extraction (optional)
- **NetworkX**: Graph analysis and visualisation

### Query Enhancement

| Query Type | Without Graph | With Graph |
|------------|---------------|------------|
| "authentication" | Semantic match only | + Related: OAuth, JWT, sessions |
| "security" | Semantic match only | + Connected: encryption, PII, auth |
| Exploration | Not possible | "Show topics related to X" |

## Implementation Tasks

- [ ] Integrate Kuzu embedded database
- [ ] Implement entity extraction pipeline
- [ ] Design graph schema (nodes, edges, properties)
- [ ] Implement relationship extraction
- [ ] Create graph building from documents
- [ ] Implement graph-enhanced retrieval
- [ ] Add graph exploration commands
- [ ] Create visualisation export (GraphML, DOT)
- [ ] Write unit tests for entity extraction
- [ ] Write integration tests for graph queries

## Success Criteria

- [ ] Entities extracted from documents automatically
- [ ] Relationships captured and queryable
- [ ] Graph queries enhance retrieval quality
- [ ] Exploration reveals non-obvious connections
- [ ] Performance acceptable (< 100ms for graph queries)
- [ ] Works offline with local NER

## Dependencies

- kuzu (embedded graph database)
- spaCy (entity extraction)
- networkx (analysis/visualisation)
- F-001 to F-008 (core pipeline)

## Technical Notes

### Graph Schema

```cypher
// Node types
CREATE NODE TABLE Document (id STRING, title STRING, path STRING)
CREATE NODE TABLE Chunk (id STRING, content STRING, doc_id STRING)
CREATE NODE TABLE Entity (id STRING, name STRING, type STRING)
CREATE NODE TABLE Topic (id STRING, name STRING)

// Relationship types
CREATE REL TABLE CONTAINS (FROM Document TO Chunk)
CREATE REL TABLE MENTIONS (FROM Chunk TO Entity)
CREATE REL TABLE RELATED_TO (FROM Entity TO Entity, weight FLOAT)
CREATE REL TABLE BELONGS_TO (FROM Entity TO Topic)
```

### Configuration

```yaml
knowledge_graph:
  enabled: true
  database: ~/.ragd/graph.kuzu

  entity_extraction:
    model: en_core_web_sm  # spaCy model
    types: [PERSON, ORG, GPE, PRODUCT, TECH]  # Entity types to extract

  relationship_extraction:
    method: cooccurrence  # cooccurrence, llm, or hybrid
    llm_model: llama3.2:3b  # if using LLM
    window_size: 3  # sentences for cooccurrence

  graph_retrieval:
    enabled: true
    hop_limit: 2  # max relationship hops
    weight_threshold: 0.3
```

### Entity Extraction

```python
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> list[Entity]:
    doc = nlp(text)
    return [
        Entity(
            name=ent.text,
            type=ent.label_,
            start=ent.start_char,
            end=ent.end_char
        )
        for ent in doc.ents
    ]
```

### Relationship Detection

```python
def extract_relationships_cooccurrence(
    chunks: list[Chunk],
    window_size: int = 3
) -> list[Relationship]:
    """Extract relationships via co-occurrence in text windows."""
    relationships = []

    for chunk in chunks:
        entities = extract_entities(chunk.content)
        # Entities mentioned together are likely related
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                relationships.append(Relationship(
                    source=e1,
                    target=e2,
                    type="RELATED_TO",
                    weight=calculate_cooccurrence_weight(e1, e2, chunk)
                ))

    return relationships
```

### Graph-Enhanced Retrieval

```python
def graph_enhanced_search(
    query: str,
    k: int = 10,
    hop_limit: int = 2
) -> list[SearchResult]:
    # Standard vector search
    initial_results = vector_search(query, k)

    # Extract entities from query
    query_entities = extract_entities(query)

    # Find related entities in graph
    related = graph.query("""
        MATCH (e1:Entity)-[r:RELATED_TO*1..{hop_limit}]-(e2:Entity)
        WHERE e1.name IN $entities
        RETURN e2.name, min(r.weight) as relevance
    """, entities=[e.name for e in query_entities])

    # Boost chunks mentioning related entities
    boosted_results = boost_by_graph(initial_results, related)

    return boosted_results
```

### CLI Commands

```bash
# Build/update knowledge graph
ragd graph build

# Explore entity relationships
ragd graph explore "authentication"
ragd graph explore "OAuth" --hops 2

# Show graph statistics
ragd graph stats

# Export for visualisation
ragd graph export --format graphml graph.graphml
```

## Related Documentation

- [State-of-the-Art Knowledge Graphs](../../research/state-of-the-art-knowledge-graphs.md) - Research basis
- [v0.8.0 Milestone](../../milestones/v0.8.0.md) - Release planning
- [F-005: Semantic Search](./F-005-semantic-search.md) - Enhanced by graph

---
