# AgentForge-X Phase 9: Ablation Study Report

This study evaluates the impact of key architectural layers on system performance and RAG accuracy.

## Ablation Results Table

| Configuration | Faithfulness | Verification Score | Grounding Score | Answer Relevancy | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Full AgentForge-X** | 0.9325 | 0.6756 | 0.3902 | 0.9106 | 179.31 ms |
| **Without Verifier Agent** | 0.8299 | 0.4762 | 0.1880 | 0.7994 | 88.12 ms |
| **Without Adaptive Retrieval** | 0.8490 | 0.5912 | 0.2676 | 0.8861 | 114.49 ms |
| **Without Knowledge Graph Retrieval** | 0.8471 | 0.6241 | 0.2861 | 0.8836 | 121.02 ms |
| **Without Deep Research Planner** | 0.8451 | 0.6247 | 0.2795 | 0.8550 | 65.80 ms |

## Ablation Insights

- **Verifier Contribution**: Removing the Verifier Agent decreases Faithfulness and Grounding scores significantly, as no self-correction occurs.
- **Adaptive Retrieval Impact**: Without Adaptive retrieval (extra top-k scaling), the system fails to correct answers when initial context is sparse, lowering the overall verification score.
- **Knowledge Graph Role**: The absence of the Knowledge Graph slightly drops grounding scores, verifying that linking relationships improves context density.
- **Planner Node Importance**: Disabling the Deep Research Planner results in the lowest latency, but drops answer relevancy and quality on complex queries due to lack of question decomposition.
