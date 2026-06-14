# Architecture

The AgentForge-X backend structure is modeled as a compiled state graph using **LangGraph**. The workflow comprises:
1. **Planner Agent**: Performs query classification, estimates depth (shallow/medium/deep), and produces up to 5 sub-questions.
2. **Research Executor**: Dispatches retrievers (Vector, Graph, or Hybrid) in parallel across the sub-questions.
3. **Evidence Aggregator**: Eliminates duplicate sentences and nodes, merging and ranking results based on similarity scores.
4. **Generator Agent**: Generates the grounded answer text incorporating inline citation mappings.
5. **Verifier Agent**: Computes the final verification score:
   $$\text{verification\_score} = 0.4 \times \text{rule\_based\_score} + 0.6 \times \text{llm\_score}$$
