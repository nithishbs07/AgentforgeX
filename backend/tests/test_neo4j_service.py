import pytest
from unittest.mock import MagicMock, patch
from app.services.graph.neo4j_service import Neo4jService, SCHEMA_STATEMENTS
from app.services.graph.ids import make_entity_id, make_chunk_id


@pytest.fixture
def offline_service():
    with patch.object(Neo4jService, "connect"):
        service = Neo4jService.__new__(Neo4jService)
        service.uri = "bolt://localhost:7687"
        service.username = "neo4j"
        service.password = "password"
        service.driver = None
        service.is_online = False
        service._schema_initialized = False
        yield service


@pytest.fixture
def online_service():
    with patch.object(Neo4jService, "connect"):
        service = Neo4jService.__new__(Neo4jService)
        service.uri = "bolt://localhost:7687"
        service.username = "neo4j"
        service.password = "password"
        service.driver = MagicMock()
        service.is_online = True
        service._schema_initialized = False
        service.health_check = MagicMock(return_value=True)
        service.query_graph = MagicMock(return_value=[])
        yield service


def test_make_entity_id_document_scoped():
    assert make_entity_id("doc-a", "TCP") == "doc-a:TCP"
    assert make_entity_id("doc-b", "TCP") == "doc-b:TCP"
    assert make_entity_id("doc-a", "TCP") != make_entity_id("doc-b", "TCP")


def test_make_chunk_id_aligned_with_chroma():
    assert make_chunk_id("abc123", 0) == "abc123_0"
    assert make_chunk_id("abc123", 5) == "abc123_5"


def test_create_entity_uses_document_scoped_id(online_service):
    online_service.create_entity("TCP", "Protocols", 0.95, "doc123", page_num=1)

    first_call = online_service.query_graph.call_args_list[0]
    params = first_call[0][1]
    assert params["entity_id"] == "doc123:TCP"
    assert params["doc_id"] == "doc123"
    assert params["name"] == "TCP"


def test_create_relationship_requires_doc_id(online_service):
    online_service.create_relationship("doc123", "TCP", "USES", "Congestion Control", 0.92)

    call = online_service.query_graph.call_args
    params = call[0][1]
    assert params["source_id"] == "doc123:TCP"
    assert params["target_id"] == "doc123:Congestion Control"
    assert params["doc_id"] == "doc123"


def test_link_chunk_mentions_stores_confidence(online_service):
    online_service.link_chunk_mentions("doc123_0", "doc123", "TCP", 0.95)

    call = online_service.query_graph.call_args
    cypher = call[0][0]
    params = call[0][1]
    assert "MENTIONS" in cypher
    assert "confidence" in cypher
    assert params["confidence"] == 0.95
    assert params["entity_id"] == "doc123:TCP"
    assert params["chunk_id"] == "doc123_0"


def test_delete_document_graph_removes_all_layers(online_service):
    online_service.delete_document_graph("doc123")

    assert online_service.query_graph.call_count == 3
    cyphers = [call[0][0] for call in online_service.query_graph.call_args_list]
    assert any("Chunk" in c for c in cyphers)
    assert any("Entity {doc_id" in c for c in cyphers)
    assert any("Document {id" in c for c in cyphers)


def test_offline_create_entity_is_noop(offline_service):
    offline_service.health_check = MagicMock(return_value=False)
    offline_service.create_entity("TCP", "Protocols", 0.95, "doc123")
    offline_service.query_graph = MagicMock()
    offline_service.create_entity("TCP", "Protocols", 0.95, "doc123")
    offline_service.query_graph.assert_not_called()


def test_offline_delete_is_noop(offline_service):
    offline_service.health_check = MagicMock(return_value=False)
    offline_service.query_graph = MagicMock()
    offline_service.delete_document_graph("doc123")
    offline_service.query_graph.assert_not_called()


def test_ensure_schema_runs_idempotently(online_service):
    session = MagicMock()
    online_service.driver.session.return_value.__enter__ = MagicMock(return_value=session)
    online_service.driver.session.return_value.__exit__ = MagicMock(return_value=False)

    online_service.ensure_schema()
    online_service.ensure_schema()

    assert session.run.call_count == len(SCHEMA_STATEMENTS)
    assert online_service._schema_initialized is True


def test_query_graph_returns_empty_when_offline(offline_service):
    offline_service.health_check = MagicMock(return_value=False)
    result = offline_service.query_graph("MATCH (n) RETURN n")
    assert result == []
