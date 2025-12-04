# ADR-0031: Knowledge Graph Storage (SQLite over Kuzu)

## Status

Accepted

## Context

F-022 Knowledge Graph Integration requires persistent storage for entities and relationships. The original design specified Kuzu, an embedded graph database designed for OLAP workloads.

During v0.8.5 implementation, we needed to decide on the storage backend:

**Option 1: Kuzu**
- Purpose-built graph database
- Cypher query language
- Graph-optimised queries
- New dependency

**Option 2: SQLite**
- Already used for metadata storage
- Familiar SQL queries
- Simpler dependency footprint
- Sufficient for local-first use case

## Decision

Use SQLite for knowledge graph storage instead of Kuzu.

## Rationale

1. **Dependency Minimisation**: ragd already uses SQLite for metadata. Adding Kuzu introduces a new compiled dependency with platform-specific binaries.

2. **Simplicity**: SQL is more familiar than Cypher. Entity/relationship queries can be expressed in standard SQL with joins.

3. **Sufficient Performance**: For personal knowledge management (thousands to tens of thousands of entities), SQLite performance is adequate. Graph traversal queries complete in < 100ms.

4. **Local-First Alignment**: SQLite is a single file, portable, and requires no background processes - aligning with ragd's local-first principles.

5. **Future Flexibility**: The storage layer can be abstracted. If graph-specific features (e.g., pathfinding algorithms) become necessary, Kuzu can be added as an optional backend later.

## Consequences

### Positive
- Simpler installation (no new binary dependencies)
- Consistent with existing SQLite usage
- Smaller distribution size
- Easier cross-platform support

### Negative
- No native Cypher query support
- Graph traversal requires multiple SQL queries or recursive CTEs
- Advanced graph algorithms (PageRank, community detection) need custom implementation

### Mitigations
- Abstract storage layer for future backend options
- Implement common graph operations (hop traversal) in Python
- Consider Kuzu as optional backend for power users in v2.x

## Implementation Notes

Schema uses three tables:
- `entities` - nodes with type and metadata
- `relationships` - edges with type and weight
- `cooccurrences` - aggregated co-occurrence counts

Graph CLI commands (v1.1) will abstract the storage layer, allowing future backend additions.

---

## Related Documentation

- [F-022: Knowledge Graph Integration](../../features/completed/F-022-knowledge-graph.md)
- [v0.8.5 Milestone](../../milestones/v0.8.5.md)
- [State-of-the-Art Knowledge Graphs](../../research/state-of-the-art-knowledge-graphs.md)

---

**Decided**: v0.8.5 implementation
