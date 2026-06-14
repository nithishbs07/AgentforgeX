import pytest
from unittest.mock import MagicMock
from app.services.graph.graph_builder import GraphBuilder
from app.services.graph.ids import make_chunk_id


def test_build_document_graph_returns_metrics():
    mock_neo4j = MagicMock()
    mock_neo4j.health_check.return_value = True

    chunks = [
        {"text": "TCP is a key transport protocol.", "page_number": 1},
        {"text": "Congestion control relies on AIMD.", "page_number": 2},
    ]

    builder = GraphBuilder(mock_neo4j)
    metrics = builder.build_document_graph(doc_id="doc123", filename="tcp.pdf", chunks=chunks)

    mock_neo4j.health_check.assert_called_once()
    mock_neo4j.ensure_schema.assert_called_once()

    assert metrics["neo4j_online"] is True
    assert metrics["chunks_processed"] == 2
    assert metrics["entities_created"] >= 2
    assert metrics["relationships_created"] >= 1
    assert metrics["latency_ms"] >= 0
    assert metrics["neo4j_calls"] > 0

    mock_neo4j.create_entity.assert_called()
    mock_neo4j.link_chunk_mentions.assert_called()
    mock_neo4j.create_relationship.assert_called()


def test_build_document_graph_uses_aligned_chunk_ids():
    mock_neo4j = MagicMock()
    mock_neo4j.health_check.return_value = True

    chunks = [{"text": "TCP uses Congestion Control.", "page_number": 1}]
    builder = GraphBuilder(mock_neo4j)
    builder.build_document_graph(doc_id="doc123", filename="tcp.pdf", chunks=chunks)

    chunk_calls = [
        call for call in mock_neo4j.query_graph.call_args_list
        if "Chunk" in call[0][0]
    ]
    assert chunk_calls
    assert chunk_calls[0][0][1]["chunk_id"] == make_chunk_id("doc123", 0)


def test_build_document_graph_offline_fallback():
    mock_neo4j = MagicMock()
    mock_neo4j.health_check.return_value = False

    builder = GraphBuilder(mock_neo4j)
    metrics = builder.build_document_graph(
        doc_id="doc123",
        filename="tcp.pdf",
        chunks=[{"text": "TCP", "page_number": 1}],
    )

    assert metrics["neo4j_online"] is False
    assert metrics["chunks_processed"] == 0
    assert metrics["entities_created"] == 0
    assert metrics["relationships_created"] == 0
    mock_neo4j.query_graph.assert_not_called()
    mock_neo4j.create_entity.assert_not_called()
