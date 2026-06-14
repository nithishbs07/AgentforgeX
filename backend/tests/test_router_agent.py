import pytest
from unittest.mock import patch, MagicMock
from app.services.agents.router_agent import RouterAgent

def test_router_agent_llm_json():
    router = RouterAgent()
    
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"route": "vector", "route_confidence": 0.95}'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        state = {"query": "What does the PDF say?"}
        res = router.run(state)
        
        assert res["route"] == "vector"
        assert res["route_confidence"] == 0.95
        assert res["execution_metadata"]["selected_route"] == "vector"
        assert res["execution_metadata"]["route_confidence"] == 0.95
        assert "router_time_ms" in res["execution_metadata"]

def test_router_agent_heuristics_fallback():
    router = RouterAgent()
    
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection refused")

        # Should match keyword 'pdf' and route to vector
        state_retrieval = {"query": "Summarize the uploaded PDF document"}
        res_retrieval = router.run(state_retrieval)
        assert res_retrieval["route"] == "vector"
        assert res_retrieval["route_confidence"] == 0.90

        # General questions with no matches should route to direct
        state_direct = {"query": "What is Python?"}
        res_direct = router.run(state_direct)
        assert res_direct["route"] == "direct"
        assert res_direct["route_confidence"] == 0.80
