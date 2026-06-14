# AgentForge-X Phase 7A: Graph Construction Benchmark

Generated: 2026-06-13T22:11:10.546369+00:00

Benchmark uses mocked Neo4j to measure graph builder orchestration overhead (entity extraction, relationship validation, Cypher call volume).

## Results

| Chunks | Latency (ms) | Entities | Relationships | Neo4j Calls | Entities/Chunk | Rels/Chunk |
|--------|--------------|----------|---------------|-------------|----------------|------------|
| 10 | 93 | 6 | 5 | 191 | 0.6 | 0.5 |
| 50 | 160 | 6 | 5 | 951 | 0.12 | 0.1 |
| 100 | 274 | 6 | 5 | 1901 | 0.06 | 0.05 |
| 500 | 1516 | 6 | 5 | 9501 | 0.01 | 0.01 |

## Notes

- Chunk IDs use `{document_id}_{index}` aligned with ChromaDB.
- Entities are document-scoped: `{document_id}:{entity_name}`.
- MENTIONS edges store entity confidence.
- Neo4j offline skips graph construction without failing ingestion.
