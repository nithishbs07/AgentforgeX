import sys
import os
import logging
import json

# Add backend directory to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.services.parser_service import ParserService
from app.services.vector_store import VectorStoreService
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reindex_docs")

def reindex_all():
    db = SessionLocal()
    doc_repo = DocumentRepository(db)
    vector_store = VectorStoreService()
    neo4j_service = Neo4jService()
    graph_builder = GraphBuilder(neo4j_service)

    print("=== AgentForge-X Document Re-indexing Process ===")
    
    # Fetch all documents
    documents = doc_repo.get_multi(limit=1000)
    print(f"Found {len(documents)} document records in SQLite.")
    
    stats = {
        "documents_processed": 0,
        "chunks_created": 0,
        "embeddings_created": 0,
        "entities_created": 0,
        "relationships_created": 0
    }
    
    # Re-initialize collection (get_or_create_collection handles this, but since we reset the directory, it's already empty)
    
    for doc in documents:
        print(f"\nProcessing document: '{doc.filename}' (ID: {doc.id})")
        print(f"  Storage path: {doc.storage_path}")
        
        if not os.path.exists(doc.storage_path):
            print(f"  [ERROR] PDF file not found on disk at: {doc.storage_path}. Skipping.")
            continue
            
        try:
            # 1. Parse PDF pages
            print("  Parsing pages...")
            pages = ParserService.parse_pdf(doc.storage_path)
            if not pages:
                print("  [WARNING] No page content extracted. Skipping.")
                continue
                
            # 2. Chunk text
            print("  Chunking page text...")
            chunks = ParserService.chunk_text(pages)
            print(f"  Generated {len(chunks)} chunks.")
            
            # 3. Embed and save to ChromaDB
            print("  Generating embeddings and saving to ChromaDB...")
            vector_store.add_chunks(doc.id, doc.filename, chunks)
            
            stats["documents_processed"] += 1
            stats["chunks_created"] += len(chunks)
            stats["embeddings_created"] += len(chunks)
            
            # 4. Build Neo4j Knowledge Graph (graceful fallback check inside)
            try:
                if neo4j_service.health_check():
                    print("  Neo4j is online. Building Knowledge Graph...")
                    graph_metrics = graph_builder.build_document_graph(doc.id, doc.filename, chunks)
                    print(f"  Graph Build Metrics: {graph_metrics}")
                    stats["entities_created"] += graph_metrics.get("entities_created", 0)
                    stats["relationships_created"] += graph_metrics.get("relationships_created", 0)
                else:
                    print("  Neo4j is offline. Skipping Knowledge Graph rebuild for this doc.")
            except Exception as ge:
                print(f"  [WARNING] Graph builder failed: {ge}")
                
            print(f"  [SUCCESS] Document '{doc.filename}' re-indexed successfully.")
            
        except Exception as e:
            print(f"  [ERROR] Ingestion pipeline failed for doc {doc.filename}: {e}")
            
    print("\n=== RE-INDEXING EXECUTION SUMMARY ===")
    print(json.dumps(stats, indent=2))
    
    # Save the reindex metrics to a json file for validation report
    with open("reindex_metrics.json", "w") as f:
        json.dump(stats, f, indent=2)
        
    db.close()

if __name__ == "__main__":
    reindex_all()
