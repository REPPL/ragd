# F-022: Knowledge Graph Integration

## Overview

**Research**: [State-of-the-Art Knowledge Graphs](../../research/state-of-the-art-knowledge-graphs.md)
**Milestone**: v0.8.5
**Priority**: P2
**Status**: ✅ Complete

## Problem Statement

Vector search finds semantically similar content but misses explicit relationships. A knowledge graph captures entities and their relationships, enabling queries like "what topics are related to authentication?" and revealing connections users might miss.

## Design Approach

### Architecture

```
Indexed Documents
    ↓
Entity Extraction (Pattern/spaCy)
    ↓
Relationship Detection (Co-occurrence)
    ↓
Knowledge Graph (SQLite)
    ↓
Graph-Enhanced Retrieval
```

### Technologies

- **SQLite**: Embedded graph storage (simpler than dedicated graph DBs)
- **Pattern matching**: Default entity extraction (fast, no dependencies)
- **spaCy**: Optional higher-quality NER (`en_core_web_sm`)
- **Co-occurrence**: Relationship detection via entity proximity

### Implementation Note

**Pragmatic Decision**: The original design specified Kuzu as the graph database. During implementation, we chose SQLite instead:

| Aspect | Kuzu | SQLite (Chosen) |
|--------|------|-----------------|
| Dependencies | New dependency | Already used |
| Complexity | Graph query language | Simple SQL |
| Local-first | Yes | Yes |
| Performance | Graph-optimised | Sufficient for local use |
| Learning curve | Cypher syntax | Familiar SQL |

SQLite provides adequate performance for personal knowledge management while keeping the dependency footprint minimal. Graph CLI commands (v1.1) will abstract the storage layer.

### Query Enhancement

| Query Type | Without Graph | With Graph |
|------------|---------------|------------|
| "authentication" | Semantic match only | + Related: OAuth, JWT, sessions |
| "security" | Semantic match only | + Connected: encryption, PII, auth |
| Exploration | Not possible | "Show topics related to X" |

## Implementation Tasks

- [x] Implement SQLite-backed graph storage
- [x] Implement entity extraction pipeline (pattern-based)
- [x] Design graph schema (entities, relationships, co-occurrence)
- [x] Implement relationship extraction via co-occurrence
- [x] Create graph building from indexed documents
- [x] Implement graph-enhanced retrieval
- [x] Write unit tests for entity extraction
- [x] Write integration tests for graph storage
- [ ] Add graph exploration CLI commands (deferred to v1.1)
- [ ] Create visualisation export (deferred to v1.1)

## Success Criteria

- [x] Entities extracted from documents automatically
- [x] Relationships captured and queryable
- [x] Graph queries enhance retrieval quality
- [x] Performance acceptable (< 100ms for graph queries)
- [x] Works offline with local extraction
- [ ] Exploration CLI reveals non-obvious connections (v1.1)

## Dependencies

- sqlite3 (Python standard library)
- spaCy (optional, for higher-quality NER)
- F-001 to F-007, F-035 (core pipeline)

## Technical Notes

### Graph Schema (SQLite)

```sql
-- Entity storage
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    doc_id TEXT,
    chunk_id TEXT,
    metadata TEXT  -- JSON
);

-- Relationship storage
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT DEFAULT 'RELATED_TO',
    weight REAL DEFAULT 1.0,
    FOREIGN KEY (source_id) REFERENCES entities(id),
    FOREIGN KEY (target_id) REFERENCES entities(id)
);

-- Co-occurrence tracking
CREATE TABLE cooccurrences (
    entity1_id TEXT NOT NULL,
    entity2_id TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (entity1_id, entity2_id)
);

-- Indexes for performance
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_relationships_source ON relationships(source_id);
CREATE INDEX idx_relationships_target ON relationships(target_id);
```

### Configuration

```yaml
knowledge_graph:
  enabled: true
  database: ~/.ragd/graph.db  # SQLite database

  entity_extraction:
    method: pattern  # pattern or spacy
    spacy_model: en_core_web_sm  # if using spacy
    types: [PERSON, ORG, GPE, PRODUCT, TECH]

  relationship_extraction:
    method: cooccurrence
    window_size: 3  # sentences for co-occurrence

  graph_retrieval:
    enabled: true
    hop_limit: 2
    weight_threshold: 0.3
```

### Entity Extraction (Pattern-Based)

```python
import re
from typing import NamedTuple

class Entity(NamedTuple):
    name: str
    type: str
    start: int
    end: int

# Pattern-based extraction (default, no dependencies)
PATTERNS = {
    'TECH': r'\b(Python|JavaScript|Docker|Kubernetes|AWS|API|REST|GraphQL)\b',
    'ORG': r'\b(Google|Microsoft|Amazon|GitHub|OpenAI|Anthropic)\b',
    # ... more patterns
}

def extract_entities_pattern(text: str) -> list[Entity]:
    entities = []
    for entity_type, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append(Entity(
                name=match.group(),
                type=entity_type,
                start=match.start(),
                end=match.end()
            ))
    return entities
```

### Entity Extraction (spaCy - Optional)

```python
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_entities_spacy(text: str) -> list[Entity]:
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

### Relationship Detection (Co-occurrence)

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

    # Find related entities via SQL
    related = db.execute("""
        SELECT DISTINCT e2.name, r.weight
        FROM entities e1
        JOIN relationships r ON e1.id = r.source_id
        JOIN entities e2 ON r.target_id = e2.id
        WHERE e1.name IN (?)
        AND r.weight >= ?
    """, [e.name for e in query_entities], weight_threshold)

    # Boost chunks mentioning related entities
    boosted_results = boost_by_graph(initial_results, related)

    return boosted_results
```

### CLI Commands (Deferred to v1.1)

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

- [ADR-0031: Knowledge Graph Storage](../../decisions/adrs/0031-knowledge-graph-storage.md) - SQLite decision
- [State-of-the-Art Knowledge Graphs](../../research/state-of-the-art-knowledge-graphs.md) - Research basis
- [v0.8.5 Milestone](../../milestones/v0.8.5.md) - Release planning
- [v1.1.0 Milestone](../../milestones/v1.1.0.md) - Graph CLI commands
- [F-005: Semantic Search](./F-005-semantic-search.md) - Enhanced by graph

---

**Status**: Complete (Foundation) - CLI commands planned for v1.1
