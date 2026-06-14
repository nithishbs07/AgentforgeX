# Publication-Ready Tables (Markdown & LaTeX)

This file contains copy-pasteable tables in both Markdown and LaTeX formats for academic papers.

---

## 1. RAG Strategy Comparison Table

### A. Markdown Format
| Configuration | Faithfulness | Relevancy | Grounding | Verification | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Vector RAG** | 0.7540 | 0.7821 | 0.2215 | 0.5451 | 65.04 ms |
| **Graph RAG** | 0.8000 | 0.8123 | 0.2654 | 0.5873 | 54.64 ms |
| **Hybrid RAG** | 0.8524 | 0.8643 | 0.3125 | 0.6283 | 69.34 ms |
| **Deep Research RAG** | **0.9332** | **0.9412** | **0.4285** | **0.6636** | 141.82 ms |

### B. LaTeX Format
```latex
\begin{table}[htbp]
\centering
\caption{Performance Comparison of RAG Retrieval Strategies}
\label{tab:rag_comparison}
\begin{tabular}{lccccc}
\hline
\textbf{Configuration} & \textbf{Faithfulness} & \textbf{Relevancy} & \textbf{Grounding} & \textbf{Verification} & \textbf{Latency (ms)} \\ \hline
Vector RAG & 0.7540 & 0.7821 & 0.2215 & 0.5451 & 65.04 \\
Graph RAG & 0.8000 & 0.8123 & 0.2654 & 0.5873 & 54.64 \\
Hybrid RAG & 0.8524 & 0.8643 & 0.3125 & 0.6283 & 69.34 \\
\textbf{Deep Research RAG} & \textbf{0.9332} & \textbf{0.9412} & \textbf{0.4285} & \textbf{0.6636} & 141.82 \\ \hline
\end{tabular}
\end{table}
```

---

## 2. Ablation Study Table

### A. Markdown Format
| Configuration | Faithfulness | Verification Score | Grounding Score | Answer Relevancy | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Full AgentForge-X** | **0.9332** | **0.6636** | **0.4285** | **0.9412** | 141.82 ms |
| **Without Verifier Agent** | 0.7937 | 0.4578 | 0.1711 | 0.8315 | 78.43 ms |
| **Without Adaptive Retrieval** | 0.8642 | 0.5985 | 0.3012 | 0.8850 | 114.28 ms |
| **Without Knowledge Graph** | 0.8912 | 0.6315 | 0.2482 | 0.8710 | 121.50 ms |
| **Without Deep Research Planner** | 0.8524 | 0.6283 | 0.3125 | 0.8643 | 69.34 ms |

### B. LaTeX Format
```latex
\begin{table}[htbp]
\centering
\caption{Ablation Study Results of AgentForge-X Subsystems}
\label{tab:ablation_study}
\begin{tabular}{lccccc}
\hline
\textbf{Configuration} & \textbf{Faithfulness} & \textbf{Verification} & \textbf{Grounding} & \textbf{Relevancy} & \textbf{Latency (ms)} \\ \hline
\textbf{Full AgentForge-X} & \textbf{0.9332} & \textbf{0.6636} & \textbf{0.4285} & \textbf{0.9412} & 141.82 \\
Without Verifier Agent & 0.7937 & 0.4578 & 0.1711 & 0.8315 & 78.43 \\
Without Adaptive Retrieval & 0.8642 & 0.5985 & 0.3012 & 0.8850 & 114.28 \\
Without Knowledge Graph & 0.8912 & 0.6315 & 0.2482 & 0.8710 & 121.50 \\
Without Deep Research Planner & 0.8524 & 0.6283 & 0.3125 & 0.8643 & 69.34 \\ \hline
\end{tabular}
\end{table}
```
