# AgentForge-X Phase 9: Demo Package Workflow Guide

This guide details how to verify, run, and demonstrate the AgentForge-X Deep Research Agent platform.

---

## 🏗️ Demo Setup

1. **Start Services**:
   Ensure Docker containers are running using the production stack:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```
   This starts:
   - Frontend Next.js UI on port `80` (mapped via Nginx)
   - Backend FastAPI API on port `80/api` (mapped via Nginx)
   - ChromaDB Vector database (port `8001`)
   - Neo4j Knowledge Graph (port `7474` HTTP, `7687` Bolt)
   - Ollama local inference container

2. **Ingest Document**:
   Upload the provided sample dataset file ([sample_dataset.txt](file:///D:/PROJECTS/agentforge-x/demo/sample_dataset.txt)) via the frontend document upload panel or via cURL:
   ```bash
   curl -X POST http://localhost/api/v1/documents/upload \
     -F "file=@demo/sample_dataset.txt"
   ```
   This triggers chunking, embedding generation in ChromaDB, and entity-relationship mapping inside Neo4j.

---

## 💬 Running Example Queries

Run the queries listed in [example_questions.json](file:///D:/PROJECTS/agentforge-x/demo/example_questions.json) to observe different RAG pathways:

### Query 1: Vector RAG (Simple Query)
> *"How does the sliding window protocol manage flow control?"*
- **Path**: Directly retrieved from ChromaDB vector space. Low latency, high grounding.

### Query 2: Hybrid Graph-Vector RAG (Complex / Structure Query)
> *"Explain how the slow start threshold (ssthresh) regulates congestion window expansion."*
- **Path**: Merges semantic chunk text and structured Neo4j nodes (Entity: `ssthresh` connected to Entity: `cwnd`).

### Query 3: Deep Research Agent RAG (Decomposed Multi-hop Query)
> *"Compare TCP and UDP connection management and transmission overheads."*
- **Path**: Decomposed into 2-3 sub-questions, retrieved in parallel, deduplicated, and verified.

---

## 📊 Evaluation & Monitoring Dashboard

1. Navigate to `http://localhost/dashboard`.
2. Click the **Research Analytics** tab to verify faithfulness and answer relevancy metrics.
3. Click the **Deployment Metrics** tab to view live HTTP request count, average server latency, uptime, and RAG strategy distributions.
