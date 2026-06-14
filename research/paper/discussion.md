# Discussion

The results demonstrate a clear trade-off between answer quality (faithfulness) and latency. Standard RAG offers low latency but suffers from hallucinations due to unstructured context retrieval. Deep Research RAG achieves near-perfect faithfulness by isolating specific questions and consolidating evidence, at the expense of a higher latency profile due to multiple LLM runs.
The addition of the Knowledge Graph helps bridge semantic gaps, specifically on multi-hop questions where pure vector distances fail to capture relationships.
