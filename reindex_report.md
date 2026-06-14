# AgentForge-X: Document Re-indexing Report

This report summarizes the re-indexing of all document chunks and their vector representations.

---

## 1. Reindexing Execution Summary

The document re-indexing script was run on 2026-06-14, reading the active database records and parsing their source PDF files:

```json
{
  "documents_processed": 1,
  "chunks_created": 15,
  "embeddings_created": 15,
  "entities_created": 0,
  "relationships_created": 0
}
```

---

## 2. Ingestion Details

1. **`COA Lab Assignment 1-24MAI0065.pdf`** (ID: `b22f0dbd-fb81-413b-ae6a-a6790dadbf37`):
   * **Status**: **SUCCESS**
   * **Pages**: 15 pages extracted.
   * **Chunks**: 15 chunks generated.
   * **Embeddings**: 15 embeddings generated using the local `nomic-embed-text` model and saved to ChromaDB.
   * **Graph**: Neo4j was offline, so Knowledge Graph ingestion was skipped.
2. **`24MAI0065 CAO ASSIGNMENT 2.pdf`** (ID: `6c59e709-7a9c-4280-bdab-215932db1c3b`):
   * **Status**: **SKIPPED**. The file was not present on disk at `backend/app/storage/10606baecc83c101cb8056656b350cd3c521e8638ed2442ec828f4653dccc980.pdf`.
