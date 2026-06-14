# Statistical Summary of RAG Strategies

This document provides a comprehensive statistical summary of the percentage improvements achieved by upgrading the retrieval configurations of AgentForge-X.

---

## 1. Metric Improvement Calculations

The metrics below represent the percentage change relative to the baseline configuration.

### A. Graph RAG vs. Vector RAG (Baseline)
- **Faithfulness**: **+6.10%** (from `0.7540` to `0.8000`)
- **Answer Relevancy**: **+3.86%** (from `0.7821` to `0.8123`)
- **Grounding Score**: **+19.82%** (from `0.2215` to `0.2654`)
- **Verification Score**: **+7.74%** (from `0.5451` to `0.5873`)
- **Latency Reduction**: **-16.00%** (from `65.04 ms` to `54.64 ms`) — *Improved speed due to smaller context payloads and precise Neo4j index lookups.*

### B. Hybrid RAG vs. Vector RAG (Baseline)
- **Faithfulness**: **+13.05%** (from `0.7540` to `0.8524`)
- **Answer Relevancy**: **+10.51%** (from `0.7821` to `0.8643`)
- **Grounding Score**: **+41.08%** (from `0.2215` to `0.3125`)
- **Verification Score**: **+15.26%** (from `0.5451` to `0.6283`)
- **Latency Change**: **+6.61%** (from `65.04 ms` to `69.34 ms`)

### C. Deep Research RAG vs. Vector RAG (Baseline)
- **Faithfulness**: **+23.77%** (from `0.7540` to `0.9332`)
- **Answer Relevancy**: **+20.34%** (from `0.7821` to `0.9412`)
- **Grounding Score**: **+93.45%** (from `0.2215` to `0.4285`) — *Nearly doubled grounding coverage.*
- **Verification Score**: **+21.74%** (from `0.5451` to `0.6636`)
- **Latency Change**: **+118.05%** (from `65.04 ms` to `141.82 ms`)

### D. Deep Research RAG vs. Hybrid RAG
- **Faithfulness**: **+9.48%** (from `0.8524` to `0.9332`)
- **Answer Relevancy**: **+8.90%** (from `0.8643` to `0.9412`)
- **Grounding Score**: **+37.12%** (from `0.3125` to `0.4285`)
- **Verification Score**: **+5.62%** (from `0.6283` to `0.6636`)
- **Latency Change**: **+104.53%** (from `69.34 ms` to `141.82 ms`)

---

## 2. Scopus-Style Results Section Text

### Section 4.2: Performance and Accuracy Evaluation

To evaluate the effectiveness of the proposed **AgentForge-X** multi-agent research architecture, we conducted a systematic comparative analysis across 100 queries for four key configurations: Vector RAG, Graph RAG, Hybrid RAG, and Deep Research RAG. 

Statistical results reveal that **Deep Research RAG** achieves the highest overall accuracy, recording a Faithfulness score of **0.9332**, Answer Relevancy of **0.9412**, Grounding Score of **0.4285**, and a Verification Score of **0.6636**. Compared to standard Vector RAG, this represents a **23.77%** increase in Faithfulness and a **93.45%** improvement in factual grounding. 

We note that **Graph RAG** exhibits the lowest average latency (**54.64 ms**), which is **16.0%** faster than standard Vector RAG. This latency reduction is attributed to Neo4j's indexed entity-relationship queries, which limit the size of retrieved contexts compared to raw vector similarity search. In contrast, **Deep Research RAG** increases latency to **141.82 ms** (+118.05% compared to Vector RAG). This latency overhead is a direct consequence of the planner node performing query decomposition and running multiple parallel retrieval processes. However, the resulting quality gains (avoiding hallucinations and enhancing relevancy) justify this trade-off for high-stakes enterprise systems.
