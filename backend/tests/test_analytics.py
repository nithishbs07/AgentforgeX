import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.core.config import settings
from app.models.models import EvaluationLog

def test_analytics_endpoints(client: TestClient, db_session):
    # Insert mock evaluation logs
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # 1. Log with retrieval route, supported, adaptive retrieval used
    log1 = EvaluationLog(
        query="Explain AIMD",
        retrieved_chunks=json.dumps([{"chunk_text": "AIMD is additive increase...", "similarity_score": 0.85}]),
        retrieved_count=1,
        top_score=0.85,
        avg_score=0.85,
        retrieval_time=0.015,
        generation_time=1.2,
        timestamp=now - timedelta(hours=1),
        verification_score=0.88,
        verification_status="SUPPORTED",
        grounding_score=0.90,
        adaptive_retrieval_used=True,
        retrieval_attempts=2,
        evidence_expansion_factor=2.0,
        verification_improvement=0.35,
        execution_metadata=json.dumps({
            "selected_route": "retrieval",
            "route_confidence": 0.95,
            "retrieval_used": True,
            "router_time_ms": 10,
            "retriever_time_ms": 15,
            "generator_time_ms": 1200,
            "verifier_time_ms": 80,
            "grounding_score_before_adaptation": 0.55,
            "grounding_score_after_adaptation": 0.90,
            "grounding_score_improvement": 0.35
        })
    )
    
    # 2. Log with direct route, partially supported, no adaptive retrieval
    log2 = EvaluationLog(
        query="Hello",
        retrieved_chunks=json.dumps([]),
        retrieved_count=0,
        top_score=0.0,
        avg_score=0.0,
        retrieval_time=0.0,
        generation_time=0.8,
        timestamp=now - timedelta(hours=5),
        verification_score=0.72,
        verification_status="PARTIALLY_SUPPORTED",
        grounding_score=0.60,
        adaptive_retrieval_used=False,
        retrieval_attempts=1,
        evidence_expansion_factor=1.0,
        verification_improvement=0.0,
        execution_metadata=json.dumps({
            "selected_route": "direct",
            "route_confidence": 0.88,
            "retrieval_used": False,
            "router_time_ms": 8,
            "retriever_time_ms": 0,
            "generator_time_ms": 800,
            "verifier_time_ms": 50
        })
    )
    
    db_session.add(log1)
    db_session.add(log2)
    db_session.commit()
    
    # Test overview endpoint
    response = client.get(f"{settings.API_V1_STR}/analytics/overview?time_range=24h")
    assert response.status_code == 200
    data = response.json()
    assert data["total_queries"] == 2
    assert data["supported_percentage"] == 50.0
    assert data["partially_supported_percentage"] == 50.0
    assert data["unsupported_percentage"] == 0.0
    assert data["adaptive_retrieval_trigger_rate"] == 50.0
    assert data["avg_verification_score"] == 0.80
    assert data["avg_grounding_score"] == 0.75
    assert data["avg_verification_improvement"] == 0.35
    
    # Test verification analytics endpoint
    response = client.get(f"{settings.API_V1_STR}/analytics/verification?time_range=all")
    assert response.status_code == 200
    data = response.json()
    assert "verification_distribution" in data
    assert "grounding_distribution" in data
    assert "improvement_distribution" in data
    assert len(data["timeline"]) == 2
    
    # Test routing analytics endpoint
    response = client.get(f"{settings.API_V1_STR}/analytics/routing?time_range=all")
    assert response.status_code == 200
    data = response.json()
    assert data["direct_route_count"] == 1
    assert data["retrieval_route_count"] == 1
    assert data["direct_route_percentage"] == 50.0
    assert data["retrieval_route_percentage"] == 50.0
    
    # Test retrieval analytics endpoint
    response = client.get(f"{settings.API_V1_STR}/analytics/retrieval?time_range=all")
    assert response.status_code == 200
    data = response.json()
    assert data["total_retrieval_queries"] == 1
    assert data["adaptive_retrieval_count"] == 1
    assert data["adaptive_retrieval_percentage"] == 100.0
    assert data["avg_evidence_expansion_factor"] == 2.0
    
    # Test latency analytics endpoint
    response = client.get(f"{settings.API_V1_STR}/analytics/latency?time_range=all")
    assert response.status_code == 200
    data = response.json()
    assert data["avg_router_time_ms"] == 9.0
    assert data["avg_retriever_time_ms"] == 7.5
    assert data["avg_generator_time_ms"] == 1000.0
    assert data["avg_verifier_time_ms"] == 65.0
    
    # Test history endpoint
    response = client.get(f"{settings.API_V1_STR}/analytics/history?time_range=all")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["query"] == "Explain AIMD"
    assert data[1]["query"] == "Hello"
