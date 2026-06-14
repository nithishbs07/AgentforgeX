# AgentForge-X Technical Interview Questions & Answers

This document lists 50 technical interview questions and detailed answers based on the architectural design, implementation, and research outcomes of the AgentForge-X platform.

---

## Part 1: System Design & Clean Architecture (Questions 1-10)

### 1. Explain the clean architecture layout of AgentForge-X and its advantages.
**Answer**: AgentForge-X decouples concerns into four distinct layers: API controllers (`app/api`), service layer (`app/services`), repositories (`app/repositories`), and core database configs (`app/core`). The API layer translates HTTP inputs into schema-validated models; the service layer runs business logic like chunk parsing, embedding lookup, and LangGraph routing; repositories abstract SQLAlchemy DB calls; and the core layer manages SQLite sessions. This isolates database and LLM changes from API and business logic, simplifying unit testing and swapping components (e.g. swapping ChromaDB for PGVector).

### 2. How are database migrations managed in the platform, and why?
**Answer**: Managed using **Alembic**. It dynamically tracks SQLAlchemy declarations in `models.py` and auto-generates schema change scripts, keeping version histories version-controlled. Database integrity remains intact across production deployments and local testing.

### 3. What is the role of Nginx in the production deployment package?
**Answer**: Nginx acts as a reverse proxy, load balancer, and security gateway. It routes public traffic on port `80`: forwarding `/api/` calls to the FastAPI backend container and static page routes `/` to the Next.js frontend container. This eliminates CORS configuration issues by exposing both services under the same domain. It also enables gzip compression and configures security headers (CSP, X-Frame-Options, X-Content-Type-Options) to protect against clickjacking and script injection.

### 4. How does the system ensure backward compatibility between Phase 8 (Deep Research) and Phase 7 (Hybrid RAG) components?
**Answer**: Through dynamic compilation in `graph.py`. The `create_agent_graph` helper checks the arguments passed: if legacy routers or adaptive retrievers are present (or if planner/executors are omitted), it builds and returns the legacy routing StateGraph. Otherwise, it compiles the new linear Deep Research StateGraph. This allows newer versions of `RAGService` to execute deep research by default while keeping legacy integration test targets fully compatible.

### 5. Why was SQLite chosen as the operational database for session logs instead of a client-server DB?
**Answer**: To keep the platform **local-first** and self-contained. SQLite has no network overhead, requires zero setup or server process administration, and operates via a single disk file, fitting local benchmarking. For scaling to multiple concurrent users, the Repository pattern makes migrating to PostgreSQL straightforward.

### 6. Detail the structure of the `evaluation_logs` SQLite table. How does it support observability?
**Answer**: It stores every user query, retrieved chunks (serialized JSON), scores, response latency, and execution metadata (as a serialized JSON string). In Phase 8/9, it was extended with fields like `planner_latency`, `research_latency`, `sub_question_count`, `faithfulness_score`, and `answer_relevancy_score` to allow granular latency tracing and quality graphing on the dashboard.

### 7. Explain the Pydantic Settings implementation in AgentForge-X. How are env overrides resolved?
**Answer**: The settings class in `config.py` inherits from `BaseSettings` (pydantic-settings). It defines system defaults (e.g., SQLite DB URLs, ChromaDB ports, Ollama model names). During initialization, it scans for local `.env` files in parent folders; any matching environment variable overrides settings defaults, allowing dynamic configs during Docker Compose container networking.

### 8. How is the Next.js frontend dashboard configured to communicate with the FastAPI backend in production?
**Answer**: The environment variable `NEXT_PUBLIC_API_URL` is set to `/api` or `http://localhost/api`. The Nginx reverse proxy routes this path internally, eliminating CORS configurations and enabling relative HTTP calls in React components.

### 9. What are the advantages of containerizing databases (ChromaDB, Neo4j) instead of calling host services?
**Answer**: It isolates filesystem changes, prevents port collisions, and standardizes environments across operating systems (Windows, Linux, macOS). It ensures that the exact versions (e.g., Neo4j v5.21, Chroma v0.5.0) are utilized, avoiding drift.

### 10. How is database connection pooling configured inside `database.py`?
**Answer**: Using SQLAlchemy's `create_engine` with `pool_pre_ping=True` and specific `connect_args` for SQLite (e.g., `check_same_thread=False`). `pool_pre_ping` runs a test query before yielding a connection to prevent stale or locked handle errors in multi-threaded environments.

---

## Part 2: Vector & Graph Retrieval (Questions 11-20)

### 11. Explain document-scoped entities in the Knowledge Graph. Why are they necessary?
**Answer**: In AgentForge-X, entity IDs are formatted as `{document_id}:{entity_name}`. This scopes nodes to their parent document, preventing cross-document contamination. For example, if two PDFs describe different definitions of "Protocol", they remain separate sub-graphs instead of merging into a single node.

### 12. How does `GraphRetriever` traverse Neo4j to collect evidence?
**Answer**: It matches query entities to the graph, and runs a **2-Hop directed traversal**: matching the entity, its neighboring entities, and parent context chunks:
`MATCH (e:Entity {id: $id})<-[:MENTIONS]-(c:Chunk) RETURN c.chunk_text`
This pulls logical contexts that are physically separated across pages but semantically connected.

### 13. What is Hybrid Retrieval, and how is it implemented?
**Answer**: Hybrid Retrieval combines semantic vector search and structured graph traversal. The query is passed to `ChromaRetriever` to fetch vector chunks, and to `GraphRetriever` to fetch Cypher-matched chunks. Both lists are returned to `HybridReranker` to fuse, deduplicate, and rank.

### 14. Explain Reciprocal Rank Fusion (RRF) and its formula.
**Answer**: RRF ranks documents fetched from multiple retrieval paths without normalizing their raw similarity scores. The score of a document $d$ is:
$$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
where $M$ is the set of retrievers, $r_m(d)$ is the rank of document $d$ in retriever $m$, and $k$ is a constant (typically 60) that dampens high-ranking outliers.

### 15. What happens when Neo4j goes offline at query time?
**Answer**: The system uses a **graceful fallback**. The `RetrieverAgent` checks Neo4j's online status via `health_check()`. If offline, it redirects graph and hybrid retrieval calls to `ChromaRetriever` (vector-only), outputting warnings to logs while remaining fully operational.

### 16. Detail how entity extraction is handled during PDF ingestion.
**Answer**: The `EntityExtractor` uses an LLM prompt to parse document text chunks and output structured JSON containing entity names, types, and confidence scores. If the LLM is offline, a regex-based fallback extracts capitalized nouns and terms.

### 17. How does the system map the hierarchy of pages and chunks in Neo4j?
**Answer**: By creating nodes and directed relationships:
`(Document)-[:HAS_PAGE]->(Page)-[:HAS_CHUNK]->(Chunk)`
This structure allows Cypher queries to query specific pages or trace adjacent sections during context reconstruction.

### 18. Why is ChromaDB's persistence directory mapped to a Docker volume in production?
**Answer**: ChromaDB runs inside a transient container. Mapping `chroma_data` ensures that document index embeddings are written to host disk space, persisting data across container restarts and builds.

### 19. How are similarity scores calculated in `ChromaRetriever`?
**Answer**: Using cosine similarity between the query embedding and chunk embeddings (generated via `nomic-embed-text` in Ollama). The retriever extracts similarity distance metrics and converts them to scores between `0` and `1`.

### 20. What is context chunk deduplication? How is it implemented in `HybridReranker`?
**Answer**: When vector search and graph search retrieve overlapping chunks, the reranker deduplicates them by checking their primary `id` (e.g. `{document_id}_{index}`). It merges duplicate entries, retaining the highest RRF ranking score.

---

## Part 3: LangGraph Agentic Workflows (Questions 21-30)

### 21. What is LangGraph? Why is it preferred over static pipelines for agent orchestration?
**Answer**: LangGraph compiles agent workflows as stateful cyclic graphs. It allows routing decisions, cycles (loops), and persistent state tracking. In AgentForge-X, this enables the Verifier Agent to route back to the Generator or Retriever dynamically if scores fail validation, which is difficult in linear pipelines.

### 22. Detail the structure of `AgentState`. How is data passed between nodes?
**Answer**: `AgentState` is a typed dictionary subclassing `TypedDict`. Nodes receive this state dictionary, run logic, and return updated keys (e.g., `answer`, `retrieved_chunks`, `verification_score`). LangGraph merges these updates back into the central state.

### 23. What is the role of the Planner Agent in Phase 8?
**Answer**: It acts as the gateway. It decides if a query requires deep research, generates up to 5 sub-questions, and determines research depth (shallow/medium/deep) and retrieval strategy (vector/graph/hybrid) per sub-question.

### 24. Explain the query decomposition heuristic fallback if Ollama is offline during planning.
**Answer**: If the LLM planner fails, the agent splits the query on punctuation and logical connectors (`and`, `but`, `compare`, `versus`). It limits sub-questions to 3, assigns default hybrid/vector retrieval modes, and sets depth to `shallow` or `medium`.

### 25. Explain the role of the Verifier Agent and the Verification Score formula.
**Answer**: It evaluates generator outputs. The combined verification score is:
$$Verification = 0.4 \times RuleScore + 0.6 \times LlmScore$$
where `RuleScore` is Jaccard keyword overlap, citation presence, and sentence coverage. If this score is $< 0.60$ on the first run, it triggers correction.

### 26. What is the difference between Verification Score and Grounding Score?
**Answer**: Grounding Score measures semantic alignment: Jaccard keyword overlap and sentence-level context mapping. Verification Score combines this rule-based grounding score with LLM checking of query-answer alignment.

### 27. Explain the Adaptive Retrieval node execution in Phase 5.
**Answer**: If verification checks fail, the system routes to the `AdaptiveRetriever` node, which doubles the lookup range (`top_k = initial_top_k * 2`), retrieves a broader context package, and routes back to the generator.

### 28. How does the system prevent infinite looping during self-correction?
**Answer**: Through loop safety counters in `AgentState`. The system enforces `max_verification_attempts = 1` and `max_retrieval_attempts = 2`. Nodes check these keys and force exit to `END` once limits are hit.

### 29. What is the difference between a legacy conditional edge and the new Deep Research linear path?
**Answer**: Legacy workflows use conditional routing edges (`Router` -> `Retriever` or `Generator`). Deep Research uses a linear flow (`Planner` -> `ResearchExecutor` -> `EvidenceAggregator` -> `Generator` -> `Verifier`), executing sub-queries in parallel before generating.

### 30. How is latency tracked for individual nodes in LangGraph?
**Answer**: Inside each node's execution block, a start timer (`time.time()`) is recorded. Before returning, the elapsed time in milliseconds is calculated and added to the `execution_metadata` dictionary.

---

## Part 4: Testing & Observability (Questions 31-40)

### 31. What is the difference between unit testing and integration testing in AgentForge-X?
**Answer**: Unit testing mocks external dependencies (e.g. patching database calls and LLM pings) to test individual node logic. Integration tests run the compiled LangGraph and API endpoints end-to-end.

### 32. Explain the mock side-effect encountered with `os.path.exists` during testing. How was it resolved?
**Answer**: Mocking `os.path.exists` globally caused `os.makedirs` to fail with `FileNotFoundError: [WinError 3]`. This occurred because `os.makedirs` uses `os.path.exists` internally to traverse folders. Resolving it required scoping the patch to the target module namespace (e.g., `scripts.backups.backup_sqlite.os.path.exists`).

### 33. Why do we track ASGI middleware latency separately from RAG service latency?
**Answer**: ASGI middleware tracks the overall HTTP request-response cycle, including router serialization and network overhead. RAG service latency tracks database lookups and LLM generation. Comparing them highlights serialization bottlenecks.

### 34. What metrics are exposed on the `/monitoring/metrics` endpoint?
**Answer**: Uptime, request volume, average latency, status code counts, and agent statistics (retrieval counts, graph usage counts, verification counts, and deep research counts).

### 35. Explain the difference between `/monitoring/liveness` and `/monitoring/readiness`.
**Answer**: `/monitoring/liveness` checks if the API server process is running. `/monitoring/readiness` verifies connections to SQLite, ChromaDB, Neo4j, and Ollama.

### 36. How is the dashboard's "Deployment Metrics" tab populated?
**Answer**: It queries `GET /api/v1/analytics/deployment`, which merges `/monitoring/metrics` stats (uptime, request counts, latencies) with historical distributions queried from `evaluation_logs`.

### 37. What is an ablation study in machine learning?
**Answer**: An evaluation method where individual components are systematically removed (ablated) from a system to isolate and measure their contributions to overall performance.

### 38. Explain the results of the AgentForge-X ablation study.
**Answer**: Removing the Verifier Agent caused the largest quality drop, reducing the Verification Score by **31.01%** and Grounding Score by **60.07%**. Removing the Planner reduced latency but lowered Answer Relevancy on complex queries.

### 39. What is Faithfulness in RAG evaluation?
**Answer**: An LLM-based metric evaluating whether the generated response is grounded in and supported by the retrieved context chunks, without introducing hallucinations.

### 40. What is Answer Relevancy in RAG evaluation?
**Answer**: Measures whether the generated answer directly addresses the user's query, penalizing redundant information.

---

## Part 5: Deployment & Production (Questions 41-50)

### 41. How does `docker-compose.prod.yml` ensure self-healing and service order?
**Answer**: Using `restart: unless-stopped` policies and health check conditions (e.g., `condition: service_healthy` for database services before starting Nginx and the backend).

### 42. Explain the security headers configured in the Nginx reverse proxy.
**Answer**:
- `X-Frame-Options "SAMEORIGIN"`: Prevents clickjacking attacks.
- `X-Content-Type-Options "nosniff"`: Disables MIME sniffing.
- `Content-Security-Policy (CSP)`: Restricts where scripts and resources can be loaded from.

### 43. Why is Nginx gzip compression enabled?
**Answer**: To compress static assets (JSON, JS, CSS) before transmission over port 80, reducing bandwidth consumption and page load times.

### 44. How does the system backup Neo4j data?
**Answer**: It queries Neo4j for all nodes and relationships, converting them into Cypher `MERGE` statements saved in a `.cypher` script. This provides a portable restore script.

### 45. What is the restore procedure for a ChromaDB backup?
**Answer**: Stop the ChromaDB service, rename the existing database directory (for safety), extract the backup zip archive into the data folder, and restart the service.

### 46. What does `pool_pre_ping=True` do in SQLAlchemy?
**Answer**: It runs a lightweight test query (e.g. `SELECT 1`) on checked-out connections. If the connection is closed or timed out, it safely reconnects, avoiding application-level errors.

### 47. Explain the CORS origins configuration.
**Answer**: The FastAPI backend parses the `BACKEND_CORS_ORIGINS` settings variable. In development, it permits wildcards (`*`); in production, it can be restricted to specific frontend domains to prevent unauthorized cross-origin requests.

### 48. What is the default model configuration in production?
**Answer**: The local Ollama service executes `llama3` for LLM generation/verification and `nomic-embed-text` for vector indexing.

### 49. How does the platform handle concurrency under SQLite?
**Answer**: By configuring connection pooling parameters, disabling same-thread checks (`check_same_thread: False`), and committing changes immediately inside transactions to minimize locks.

### 50. How does the dashboard fetch historical data?
**Answer**: It queries `/analytics/overview`, `/analytics/history`, `/analytics/latency`, and `/analytics/research`, which parse the SQLite `evaluation_logs` database with time-range filters (24h, 7d, 30d, all).
