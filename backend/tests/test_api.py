from fastapi.testclient import TestClient
from app.core.config import settings

def test_health_check(client: TestClient):
    """Verifies that the /health endpoint is operational."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_sessions_crud(client: TestClient):
    """Verifies complete CRUD lifecycle operations for chat sessions."""
    # Create Session
    payload = {"title": "Test Chat Session"}
    response = client.post(f"{settings.API_V1_STR}/sessions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Chat Session"
    assert "id" in data
    session_id = data["id"]

    # List Sessions
    response = client.get(f"{settings.API_V1_STR}/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) >= 1
    assert any(s["id"] == session_id for s in sessions)

    # Get Session with Details
    response = client.get(f"{settings.API_V1_STR}/sessions/{session_id}")
    assert response.status_code == 200
    session_details = response.json()
    assert session_details["title"] == "Test Chat Session"
    assert "messages" in session_details
    assert len(session_details["messages"]) == 0

    # Update Session title
    update_payload = {"title": "Updated Session Title"}
    response = client.put(f"{settings.API_V1_STR}/sessions/{session_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Session Title"

    # Delete Session
    response = client.delete(f"{settings.API_V1_STR}/sessions/{session_id}")
    assert response.status_code == 200
    
    # Retrieve deleted session should return 404
    response = client.get(f"{settings.API_V1_STR}/sessions/{session_id}")
    assert response.status_code == 404

def test_list_documents_initially_empty(client: TestClient):
    """Verifies that document index list is initially empty."""
    response = client.get(f"{settings.API_V1_STR}/documents")
    assert response.status_code == 200
    assert response.json() == []
