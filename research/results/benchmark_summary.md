# AgentForge-X Phase 9: Benchmark Summary Report

Executed on: 2026-06-14T16:45:46.134546 (Simulator=True, Queries/Strategy=2)

## Comparative Performance Matrix

| Strategy | Faithfulness | Relevancy | Grounding | Verification | Precision | Recall | Latency (ms) | Avg Evidence | Avg Sub-Q |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Vector RAG** | 0.7034 | 0.8003 | 0.1796 | 0.5184 | 0.7305 | 0.7126 | 64.60 ms | 4.0 | 1.0 |
| **Graph RAG** | 0.7717 | 0.7632 | 0.2547 | 0.6076 | 0.7699 | 0.6929 | 49.40 ms | 3.0 | 1.0 |
| **Hybrid RAG** | 0.8718 | 0.8400 | 0.3281 | 0.6091 | 0.8116 | 0.7837 | 76.15 ms | 5.0 | 1.0 |
| **Deep Research RAG** | 0.9344 | 0.9249 | 0.3805 | 0.6884 | 0.9017 | 0.9176 | 118.06 ms | 11.0 | 4.0 |

## Strategic Key Findings

1. **Deep Research Accuracy Boost**: Deep Research RAG achieves the highest faithfulness and verification levels through multi-step decomposition.
2. **Knowledge Graph Utility**: Graph and Hybrid RAG provide superior context recall and precision compared to pure vector retrievals.
3. **Latency Profile**: Deep Research RAG incurs higher execution times due to nested query routing and synthesis steps.
