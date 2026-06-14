import pytest
from unittest.mock import patch, MagicMock
from app.services.agents.graph import create_agent_graph
from app.services.retrieval import BaseRetriever

class MockRetriever(BaseRetriever):
    def retrieve(self, query: str, top_k: int = 5):
        return [{"chunk_text": f"Mock chunk for {query}", "document_id": "doc1", "filename": "test.pdf", "page_number": 1, "similarity_score": 0.88}]

def test_research_workflow_full_run():
    # 1. Setup mock Ollama responses
    call_index = 0
    def mock_post_side_effect(url, json=None, **kwargs):
        nonlocal call_index
        prompt = json.get("prompt", "")
        res_val = ""
        
        if "decompose" in prompt or "sub_questions" in prompt or "Planner" in prompt:
            res_val = '{"main_query": "Test query", "sub_questions": ["SubQ1", "SubQ2"], "research_depth": "medium", "retrieval_modes": ["vector", "vector"]}'
        elif "Determine whether the generated answer is supported" in prompt or "Retrieved Evidence:" in prompt:
            res_val = '{"score": 0.90, "status": "SUPPORTED", "reason": "Perfect match."}'
        elif "Analyze the generated answer and the context" in prompt:
            res_val = '{"score": 0.95}'
        elif "Analyze the user query and the generated answer" in prompt:
            res_val = '{"score": 0.92}'
        elif "Source 1" in prompt or "Source 2" in prompt:
            res_val = "Generated deep research answer text."
        else:
            res_val = "Default fallback mock."

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": res_val}
        mock_resp.raise_for_status = MagicMock()
        call_index += 1
        return mock_resp

    retriever = MockRetriever()
    from app.services.agents.planner_agent import PlannerAgent
    from app.services.agents.research_executor import ResearchExecutor
    from app.services.agents.evidence_aggregator import EvidenceAggregator
    from app.services.agents.generator_agent import GeneratorAgent
    from app.services.agents.verifier_agent import VerifierAgent

    planner = PlannerAgent()
    executor = ResearchExecutor(retriever)
    aggregator = EvidenceAggregator()
    generator = GeneratorAgent()
    verifier = VerifierAgent()

    graph = create_agent_graph(planner=planner, research_executor=executor, evidence_aggregator=aggregator, generator=generator, verifier=verifier)

    initial_state = {
        "query": "How does sliding window flow control prevent receiver buffer overflow?",
        "session_id": "session123",
        "route": "deep_research",
        "route_confidence": 1.0,
        "retrieved_chunks": [],
        "citations": [],
        "answer": "",
        "confidence_score": 0.0,
        "verification_score": 0.0,
        "grounding_score": 0.0,
        "verification_status": "UNSUPPORTED",
        "verification_reason": "",
        "verified": False,
        "verification_attempts": 0,
        "adaptive_retrieval_used": False,
        "retrieval_attempts": 1,
        "initial_retrieved_count": 0,
        "final_retrieved_count": 0,
        "evidence_expansion_factor": 1.0,
        "adaptive_retrieval_reason": "",
        "verification_score_before_adaptation": 0.0,
        "verification_score_after_adaptation": 0.0,
        "verification_improvement": 0.0,
        "retrieval_mode": "hybrid",
        "graph_entities": [],
        "graph_relationships": [],
        "graph_results": [],
        "hybrid_used": True,
        "graph_confidence": 0.0,
        "graph_hit_count": 0,
        
        # New keys
        "sub_questions": [],
        "research_depth": "shallow",
        "retrieval_modes": [],
        "evidence_package": {},
        "planner_latency": 0.0,
        "research_latency": 0.0,
        "aggregation_latency": 0.0,
        "faithfulness_score": 0.0,
        "answer_relevancy_score": 0.0,
        "execution_metadata": {}
    }

    with patch("requests.post", side_effect=mock_post_side_effect):
        with patch("app.services.embedding_service.is_ollama_online", return_value=True):
            with patch("app.services.graph.neo4j_service.Neo4jService.health_check", return_value=True):
                final_state = graph.invoke(initial_state)
                
                assert final_state["answer"] == "Generated deep research answer text."
                assert final_state["sub_questions"] == ["SubQ1", "SubQ2"]
                assert final_state["research_depth"] == "medium"
                assert len(final_state["retrieved_chunks"]) == 2
                assert final_state["retrieved_chunks"][0]["chunk_text"] == "Mock chunk for SubQ1"
                assert final_state["retrieved_chunks"][1]["chunk_text"] == "Mock chunk for SubQ2"
                
                # Check metrics
                assert final_state["verification_score"] == pytest.approx(0.66, abs=0.01)
                assert final_state["verification_status"] == "PARTIALLY_SUPPORTED"
                assert final_state["planner_latency"] >= 0
                assert final_state["research_latency"] >= 0
                assert final_state["aggregation_latency"] >= 0


