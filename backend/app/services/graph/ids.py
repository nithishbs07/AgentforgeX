"""Shared identifiers for ChromaDB and Neo4j graph nodes."""


def make_chunk_id(document_id: str, index: int) -> str:
    """Standard chunk ID: {document_id}_{index} (aligned with ChromaDB)."""
    return f"{document_id}_{index}"


def make_entity_id(document_id: str, name: str) -> str:
    """Document-scoped entity ID: {document_id}:{name}."""
    return f"{document_id}:{name}"


def make_page_id(document_id: str, page_number: int) -> str:
    """Page node ID within a document."""
    return f"{document_id}_p{page_number}"
