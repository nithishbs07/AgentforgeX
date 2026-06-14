# Subsystem Component Contribution Analysis

This document identifies and ranks the strongest architectural contributors in the AgentForge-X system based on empirical ablation study data.

---

## 1. Subsystem Contributor Ranking

The table below ranks components based on their negative impact on the **Verification Score** (primary truthfulness and trust metric) and **Faithfulness** when ablated (removed) from the **Full AgentForge-X** pipeline.

| Rank | Subsystem | Verification Drop (%) | Faithfulness Drop (%) | Primary Metric Impact |
| :--- | :--- | :---: | :---: | :--- |
| **1** | **Verifier Agent** | **-31.01%** | **-14.95%** | **Strongest Contributor**: Enforces logical/factual safety checks and triggers self-correction loops. |
| **2** | **Adaptive Retrieval** | **-9.81%** | **-7.39%** | **Key Context Booster**: Scaling context window (`top_k` expansion) resolves sparse initial retrieval. |
| **3** | **Deep Research Planner** | **-5.32%** | **-8.66%** | **Factual Structurer**: Decomposes complex queries to match relevant index aspects. |
| **4** | **Knowledge Graph** | **-4.84%** | **-4.50%** | **Entity Linking**: Contributes majorly to context grounding (**-42.08%** drop when removed). |

---

## 2. Contributor Analysis Details

### A. Verifier Agent
The Verifier Agent acts as the gateway to final generation. When removed, the system lacks any feedback mechanism, permitting hallucinated segments and loose query-alignments to pass. 
- **Factual Grounding**: Without the verifier, Grounding Score drops by **60.07%** (from `0.4285` to `0.1711`), showing it is critical for factual generation.

### B. Adaptive Retrieval
Adaptive Retrieval provides the necessary context capacity expansion during verification failures. 
- **Context Buffering**: Its absence restricts the system to initial retrieval constraints, preventing the generator from acquiring the correct facts on verification retry.

### C. Deep Research Planner
The query planner decomposes multi-hop user requests. 
- **Query Resolution**: Removing the planner drops Answer Relevancy by **8.17%** (from `0.9412` to `0.8643`) because complex queries are executed as single-stage lookups, missing supplementary domain details.

### D. Knowledge Graph Retrieval
Neo4j knowledge graphs link conceptual connections.
- **Relational Context**: Removing graph retrieval causes a **42.08%** drop in Grounding Score, demonstrating that graph-structured relationships provide critical evidence that vector distance matches miss.
