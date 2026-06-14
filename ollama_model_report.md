# AgentForge-X: Ollama Model Report

This report summarizes the verified status of Ollama models on the CPU-only host machine.

---

## 1. Verified Models List

The local Ollama instance (`http://127.0.0.1:11434`) was queried successfully, confirming the presence of the following models:

| Model Name | Parameter Size | File Size (MB) | Embedding Dimensions | Capabilities | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`qwen2.5-coder:7b`** | 7.6B | ~4,466 MB | 3,584 | text-generation | **Active & Ready** |
| **`nomic-embed-text:latest`** | 137M | ~261.6 MB | 768 | embeddings | **Active & Ready** |

---

## 2. Model Roles in AgentForge-X

1. **`qwen2.5-coder:7b`**:
   * **Role**: Primary Language Model.
   * **Scope**: GeneratorAgent (answer production), PlannerAgent (query decomposition), VerifierAgent (truthfulness scoring), RouterAgent (query classification), and Graph Extraction (entities/relationships parsing).
   * **Optimization**: Excellent local reasoning and code/JSON production within 8GB RAM constraints.
2. **`nomic-embed-text`**:
   * **Role**: Embedding Model.
   * **Scope**: Vector Store Service (ChromaDB document ingestion), Query Embedding (similarity queries).
   * **Optimization**: Extremely fast BERT-based architecture with 768-dimension output.
