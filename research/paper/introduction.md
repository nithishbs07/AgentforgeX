# Introduction

Modern Large Language Models (LLMs) suffer from hallucinations—generating factually incorrect but fluent text. Retrieval-Augmented Generation (RAG) reduces this issue by feeding external document contexts directly into the model's prompt. However, static RAG architectures are limited: they retrieve a fixed set of chunks, struggle with complex multi-hop queries, and lack self-correcting feedback loops.

To address these limitations, we present AgentForge-X. AgentForge-X treats retrieval not as a single-turn database look-up, but as an agentic, iterative deep research process. When a user submits a query, it is analyzed by a query planner, decomposed into sub-questions, retrieved from vector space and document-scoped knowledge graphs, merged and deduplicated, and verified. 
