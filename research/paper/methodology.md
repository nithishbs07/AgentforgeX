# Methodology

The AgentForge-X research methodology is built on three key architectural principles:
1. **Query Decomposition**: Linear queries are split into specialized sub-queries using a structured JSON LLM planner to expose latent aspects.
2. **Hybrid Multi-Source Evidence Extraction**: Context is retrieved by intersecting vector similarity (ChromaDB) and structured Entity-Relationship lookups (Neo4j) to capture semantic and logical relationships.
3. **Verification-Aware Generation & Self-Correction**: The verifier calculates citation presence, keyword overlap, and LLM-based truthfulness, triggering dynamic top-k evidence expansion if quality falls below set thresholds.
