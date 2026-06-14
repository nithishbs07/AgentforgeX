import chromadb
import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.graph.ids import make_chunk_id

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        # Initialize standard Chroma persistent client
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        self.embedding_service = EmbeddingService()
        self.collection_name = "agentforge_documents"
        
        # We manually compute embeddings via Ollama to keep alignment with local models
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, document_id: str, filename: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Calculates embeddings for each chunk and indexes them into ChromaDB.
        """
        if not chunks:
            logger.warning("No chunks to add to VectorStore")
            return
            
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = make_chunk_id(document_id, idx)
            text = chunk["text"]
            page_num = chunk["page_number"]
            
            # Generate embedding representation via Ollama
            vector = self.embedding_service.get_embedding(text)
            
            ids.append(chunk_id)
            documents.append(text)
            embeddings.append(vector)
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "page_number": page_num
            })
            
        # Write vectors to Chroma storage
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Ingested {len(chunks)} chunks into Chroma DB '{self.collection_name}' for doc {document_id}")

    def query_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Queries Chroma for similar document chunks.
        """
        query_vector = self.embedding_service.get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        formatted_results = []
        if not results or not results["documents"] or len(results["documents"]) == 0:
            return formatted_results
            
        # Parse query lists
        docs_list = results["documents"][0]
        meta_list = results["metadatas"][0]
        dist_list = results.get("distances", [[]])[0]
        ids_list = results["ids"][0]
        
        for i in range(len(docs_list)):
            distance = dist_list[i] if idx_in_bounds(dist_list, i) else 0.0
            formatted_results.append({
                "id": ids_list[i],
                "text": docs_list[i],
                "metadata": meta_list[i],
                "score": float(1.0 - distance)  # Cosine similarity metric
            })
            
        return formatted_results

    def delete_document_chunks(self, document_id: str) -> None:
        """
        Deletes vector records by document metadata filter.
        """
        self.collection.delete(where={"document_id": document_id})
        logger.info(f"Deleted vector chunks for document_id: {document_id}")

def idx_in_bounds(lst: list, idx: int) -> bool:
    return 0 <= idx < len(lst)
