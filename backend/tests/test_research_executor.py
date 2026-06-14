import pytest
from unittest.mock import patch, MagicMock
from app.services.agents.research_executor import ResearchExecutor
from app.services.retrieval import BaseRetriever

class MockRetriever(BaseRetriever):
    def retrieve(self, query: str, top_k: int = 5):
        return [{"chunk_text": f"Mock chunk for {query}", "document_id": "doc1", "filename": "test.pdf", "page_number": 1, "similarity_score": 0.85}]

def test_research_executor_success():
    retriever = MockRetriever()
    executor = ResearchExecutor(retriever)
    
    state = {
        "sub_questions": ["What is congestion window?", "Explain slow start."],
        "retrieval_modes": ["vector", "hybrid"],
        "execution_metadata": {}
    }

    # Mock Graph and Hybrid retrievers
    mock_hybrid_res = {
        "retrieved_chunks": [{"chunk_text": "Hybrid context", "document_id": "doc2", "filename": "hybrid.pdf", "page_number": 2, "similarity_score": 0.90}],
        "entities": [{"name": "TCP"}],
        "relationships": [{"source": "TCP", "type": "USES", "target": "AIMD"}],
        "graph_confidence": 0.88,
        "graph_hit_count": 2
    }

    with patch("app.services.graph.neo4j_service.Neo4jService.health_check", return_value=True):
        with patch("app.services.graph.hybrid_retriever.HybridRetriever.retrieve", return_value=mock_hybrid_res):
            result = executor.run(state)
            
            assert "evidence_package" in result
            pkg = result["evidence_package"]
            assert pkg["total_chunks_retrieved"] == 2
            
            results_dict = pkg["sub_questions_results"]
            assert "What is congestion window?" in results_dict
            assert "Explain slow start." in results_dict
            
            assert results_dict["What is congestion window?"]["mode"] == "vector"
            assert results_dict["Explain slow start."]["mode"] == "hybrid"
            assert len(results_dict["Explain slow start."]["chunks"]) == 1
            assert results_dict["Explain slow start."]["chunks"][0]["chunk_text"] == "Hybrid context"

def test_research_executor_neo4j_offline_fallback():
    retriever = MockRetriever()
    executor = ResearchExecutor(retriever)
    
    state = {
        "sub_questions": ["Query relationship"],
        "retrieval_modes": ["graph"],
        "execution_metadata": {}
    }

    with patch("app.services.graph.neo4j_service.Neo4jService.health_check", return_value=False):
        result = executor.run(state)
        pkg = result["evidence_package"]
        res = pkg["sub_questions_results"]["Query relationship"]
        
        # Falls back to vector, which runs against retriever returning Mock chunk
        assert res["actual_mode"] == "vector"
        assert res["chunks"][0]["chunk_text"] == "Mock chunk for Query relationship"
