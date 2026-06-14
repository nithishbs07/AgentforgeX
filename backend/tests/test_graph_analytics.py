import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.core.config import settings


def test_graph_analytics_offline_returns_zeros(client: TestClient):
    with patch("app.services.graph.neo4j_service.Neo4jService") as mock_cls:
        mock_neo4j = MagicMock()
        mock_neo4j.health_check.return_value = False
        mock_cls.return_value = mock_neo4j

        response = client.get(f"{settings.API_V1_STR}/analytics/graph?time_range=all")
        assert response.status_code == 200
        data = response.json()

        assert data["neo4j_online"] is False
        assert data["entity_count"] == 0
        assert data["relationship_count"] == 0
        assert data["entity_growth"] == []
        assert data["relationship_growth"] == []
