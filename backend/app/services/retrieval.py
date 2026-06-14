from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.services.vector_store import VectorStoreService

class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Abstract method to query external index resources and retrieve document chunks.
        """
        pass

class ChromaRetriever(BaseRetriever):
    def __init__(self, vector_store: VectorStoreService = None):
        # Inject VectorStoreService if provided, otherwise lazy instantiate
        self.vector_store = vector_store or VectorStoreService()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB vector database and formats response with standard RAG fields.
        """
        raw_results = self.vector_store.query_similar(query, top_k=top_k)
        
        formatted = []
        for res in raw_results:
            metadata = res.get("metadata", {})
            formatted.append({
                "chunk_text": res.get("text", ""),
                "document_id": str(metadata.get("document_id", "")),
                "filename": str(metadata.get("filename", "")),
                "page_number": int(metadata.get("page_number", 0) or 0),
                "similarity_score": float(res.get("score", 0.0) or 0.0)
            })
        return formatted

class BM25Retriever(BaseRetriever):
    """
    Placeholder architecture stub for sparse keyword BM25 retriever.
    """
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError("BM25Retriever is not implemented yet.")

class Neo4jRetriever(BaseRetriever):
    """
    Placeholder architecture stub for graph-based Neo4j graph retriever.
    """
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError("Neo4jRetriever is not implemented yet.")

class HybridRetriever(BaseRetriever):
    """
    Placeholder architecture stub for combined keyword + vector hybrid retriever.
    """
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError("HybridRetriever is not implemented yet.")
