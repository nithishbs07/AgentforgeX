# Results

Our benchmark evaluates four retrieval configurations across 100 queries each (400 queries total).

## Comparative Evaluation Matrix

| Configuration | Faithfulness | Grounding | Verification | Average Latency (ms) | Avg Evidence | Avg Sub-Q |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Standard Vector RAG** | 0.7589 | 0.2131 | 0.5451 | 61.0 ms | 4.1 | 1.0 |
| **Graph RAG** | 0.8030 | 0.2645 | 0.5901 | 52.4 ms | 3.0 | 1.0 |
| **Hybrid RAG** | 0.8460 | 0.3160 | 0.6324 | 67.4 ms | 5.6 | 1.0 |
| **Deep Research RAG** | **0.9333** | **0.4113** | **0.6719** | 139.1 ms | 8.8 | 3.0 |

