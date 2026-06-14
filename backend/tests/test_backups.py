import os
import shutil
import pytest
from unittest.mock import patch, MagicMock

from scripts.backups.backup_sqlite import run_backup as run_sqlite_backup
from scripts.backups.backup_chromadb import run_backup as run_chroma_backup
from scripts.backups.backup_neo4j import run_backup as run_neo4j_backup

@patch("shutil.copy2")
@patch("scripts.backups.backup_sqlite.os.path.exists", return_value=True)
def test_sqlite_backup_flow(mock_exists, mock_copy):
    # Verify that run_sqlite_backup calls shutil.copy2 with correct parameters
    with patch("sys.exit") as mock_exit:
        run_sqlite_backup()
        assert mock_copy.called
        assert not mock_exit.called

@patch("scripts.backups.backup_chromadb.zip_directory")
@patch("scripts.backups.backup_chromadb.os.path.exists", return_value=True)
def test_chroma_backup_flow(mock_exists, mock_zip):
    # Verify that zip_directory is called
    with patch("sys.exit") as mock_exit:
        run_chroma_backup()
        assert mock_zip.called
        assert not mock_exit.called

@patch("app.services.graph.neo4j_service.Neo4jService.health_check", return_value=True)
@patch("app.services.graph.neo4j_service.Neo4jService.query_graph")
def test_neo4j_backup_flow(mock_query, mock_health):
    # Mock data returns
    mock_query.side_effect = [
        [{"labels": ["Entity"], "props": {"id": "1", "name": "Test"}}], # Nodes
        [{"source_labels": ["Entity"], "source_id": "1", 
          "target_labels": ["Entity"], "target_id": "2", 
          "rel_type": "USES", "rel_props": {"weight": 0.9}}] # Rels
    ]
    
    with patch("builtins.open", create=True) as mock_open:
        with patch("sys.exit") as mock_exit:
            run_neo4j_backup()
            assert mock_open.called
            assert not mock_exit.called
