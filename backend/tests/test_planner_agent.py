import pytest
from unittest.mock import patch, MagicMock
from app.services.agents.planner_agent import PlannerAgent

def test_planner_agent_online_json():
    agent = PlannerAgent()
    state = {"query": "Compare TCP and UDP in congestion control"}

    mock_response = {
        "main_query": "Compare TCP and UDP in congestion control",
        "sub_questions": [
            "How does TCP handle congestion control?",
            "How does UDP handle congestion control?",
            "What are the differences between TCP and UDP?"
        ],
        "research_depth": "deep",
        "retrieval_modes": ["vector", "graph", "hybrid"]
    }

    with patch("app.services.embedding_service.is_ollama_online", return_value=True):
        with patch("requests.post") as mock_post:
            mock_post_resp = MagicMock()
            mock_post_resp.json.return_value = {"response": '{"main_query": "Compare TCP and UDP in congestion control", "sub_questions": ["How does TCP handle congestion control?", "How does UDP handle congestion control?", "What are the differences between TCP and UDP?"], "research_depth": "deep", "retrieval_modes": ["vector", "graph", "hybrid"]}'}
            mock_post_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_resp

            result = agent.run(state)
            
            assert len(result["sub_questions"]) == 3
            assert result["research_depth"] == "deep"
            assert result["retrieval_modes"] == ["vector", "graph", "hybrid"]
            assert result["planner_latency"] > 0

def test_planner_agent_offline_fallback():
    agent = PlannerAgent()
    state = {"query": "What is the relationship between AIMD and slow start?"}

    with patch("app.services.embedding_service.is_ollama_online", return_value=False):
        result = agent.run(state)
        
        assert len(result["sub_questions"]) >= 2
        assert "AIMD" in result["sub_questions"][0] or "AIMD" in result["sub_questions"][1]
        assert "graph" in result["retrieval_modes"] or "hybrid" in result["retrieval_modes"]
        assert result["research_depth"] == "medium"

def test_planner_agent_limit_constraints():
    agent = PlannerAgent()
    state = {"query": "Simple query"}

    # Mock response with more than 5 questions
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"response": '{"sub_questions": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"], "retrieval_modes": ["vector", "vector", "vector", "vector", "vector", "vector", "vector"], "research_depth": "shallow"}'}

    
    with patch("app.services.embedding_service.is_ollama_online", return_value=True):
        with patch("requests.post", return_value=mock_post_resp):
            result = agent.run(state)
            
            assert len(result["sub_questions"]) == 5
