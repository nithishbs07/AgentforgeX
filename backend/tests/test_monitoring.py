import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.monitoring.metrics_registry import metrics_registry

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

def test_liveness_endpoint():
    response = client.get("/monitoring/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"

def test_readiness_endpoint():
    # Since during test execution Neo4j might be mocked or offline, 
    # we assert either 200 or 503 depending on check states. 
    response = client.get("/monitoring/readiness")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "dependencies" in data
    assert "sqlite" in data["dependencies"]

def test_metrics_endpoint():
    response = client.get("/monitoring/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "request_count" in data
    assert "average_latency_ms" in data

def test_middleware_request_counts():
    initial_count = metrics_registry.request_count
    
    # Hit some endpoint
    client.get("/monitoring/liveness")
    
    # The middleware registers standard HTTP scope calls
    # Check that in-memory registry increments
    assert metrics_registry.request_count > initial_count
