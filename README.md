# AgentForge-X

Deep Research Multi-Agent RAG Platform

AgentForge-X is a production-grade, local-first Deep Research platform powered by collaborative multi-agent reasoning, semantic vector search, and graph-based grounding. By decomposing complex prompts into plan steps and verifying statements against retrieved documents, AgentForge-X guarantees factual accuracy and eliminates hallucinations.

---

## Features

* **Deep Research Workflow**: Automatically decomposes complex prompts into parallel sub-questions.
* **Query Planning**: Planner Agent plans searches dynamically based on research depth.
* **Evidence Aggregation**: Deduplicates, merges, and ranks retrieved context fragments.
* **Citation Tracking**: Fully grounded citation mapping with page numbers and confidence ratings.
* **Verification Agent**: Self-correcting verifier checks factual assertions against retrieved evidence.
* **Gemini Integration**: Utilizes `gemini-2.5-flash` for multi-agent reasoning and final generation.
* **ChromaDB Retrieval**: Local vector store for semantic indexing and search.
* **Neo4j Knowledge Graph**: Optional entity relationship graph matching for semantic context.
* **FastAPI Backend**: Asynchronous endpoints for RAG execution, chat sessions, and readiness monitoring.
* **Next.js Frontend**: Sleek dashboard metrics and responsive chat workspace.
* **Research Analytics Dashboard**: System evaluation tracking (faithfulness, latency, routing accuracy).

---

## Architecture

```text
       User Query
           │
           ▼
     ┌───────────┐
     │  Router   ├───────────────┐ (Direct Route)
     └─────┬─────┘               │
           │ (Deep Research)     ▼
           ▼                ┌───────────┐
     ┌───────────┐          │ Generator │
     │  Planner  │          └─────┬─────┘
     └─────┬─────┘                │
           ▼                      ▼
     ┌───────────┐          ┌───────────┐
     │ Retriever │          │ Verifier  │
     └─────┬─────┘          └─────┬─────┘
           ▼                      ▼
     ┌───────────┐           Final Answer
     │ Aggregator│
     └─────┬─────┘
           ▼
     ┌───────────┐
     │ Generator │
     └─────┬─────┘
           │
           ▼
     ┌───────────┐
     │ Verifier  │
     └─────┬─────┘
           ▼
      Final Answer
```

---

## Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS v4
- **Animations**: Framer Motion
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Workflow Orchestration**: LangGraph
- **Database**: SQLite (SQLAlchemy ORM)
- **Monitoring**: Custom Readiness Endpoint

### AI & Vector Stores
- **Models**: Google Gemini (`gemini-2.5-flash`), Ollama (`qwen2.5-coder:7b`)
- **Embeddings**: Ollama (`nomic-embed-text`)
- **Vector DB**: ChromaDB
- **Graph DB**: Neo4j (Optional)

---

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama (installed and running locally)

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install npm packages:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Environment Variables

Create a `.env` file in the root directory and the `backend` directory matching the `.env.example` structure:

```env
PROJECT_NAME="AgentForge-X"
LLM_PROVIDER="gemini"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GEMINI_MODEL="gemini-2.5-flash"
GEMINI_TEMPERATURE=0.2
GEMINI_TIMEOUT=120

OLLAMA_BASE_URL="http://127.0.0.1:11434"
OLLAMA_LLM_MODEL="qwen2.5-coder:7b"
OLLAMA_EMBEDDING_MODEL="nomic-embed-text"

DATABASE_URL="sqlite:///./agentforge.db"
CHROMA_PERSIST_DIRECTORY="./chromadb_data"
NEO4J_URI="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="password"
```

---

## Screenshots

Below are the key UI views of AgentForge-X:

### Chat Workspace
![Chat Workspace](docs/screenshots/chat.png)

### Ingestion & Documents
![Ingestion & Documents](docs/screenshots/home.png)

### System Observability Dashboard
![System Evaluation Dashboard](docs/screenshots/dashboard.png)

*(Screenshots can be added under the `docs/screenshots/` directory)*

---

## Current Status

- **Backend**: Stable (FastAPI router & evaluation engine)
- **Deep Research**: Active (LangGraph parallel sub-agent workflows)
- **Gemini**: Working (Production integrations with Gemini API)
- **ChromaDB**: Working (Local vector embeddings ingestion)
- **Neo4j**: Optional (Entity relationship retrieval mappings)
- **Frontend**: Active (Next.js with clean responsive Tailwind UI)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
