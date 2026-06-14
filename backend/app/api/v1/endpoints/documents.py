import os
import hashlib
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.api.deps import get_document_repo
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import Document
from app.services.parser_service import ParserService
from app.services.vector_store import VectorStoreService
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)
router = APIRouter()
vector_store_service = VectorStoreService()
neo4j_service = Neo4jService()
graph_builder = GraphBuilder(neo4j_service)

# Storage directory for ingested PDF uploads relative to this file
API_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(os.path.dirname(API_DIR), "storage")

@router.post("/upload", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """
    Ingests a PDF document.
    Calculates checksum, parses pages, chunks content, generates embeddings,
    and indexes into vector database (Chroma) and SQLite.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )

    # Ensure folder structure for storage is present
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Read bytes to verify content hash and avoid duplicates
    try:
        content = await file.read()
        checksum = hashlib.sha256(content).hexdigest()
    except Exception as e:
        logger.error(f"Failed to read upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file."
        )
    
    # Check duplicate
    existing_doc = doc_repo.get_by_checksum(checksum)
    if existing_doc:
        logger.info(f"File {file.filename} with hash {checksum} already ingested")
        return existing_doc
        
    # Write to local disk storage
    file_path = os.path.join(UPLOAD_DIR, f"{checksum}.pdf")
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"Failed to write file to storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write document to backend storage."
        )
        
    try:
        # Extract content & structure
        pages = ParserService.parse_pdf(file_path)
        if not pages:
            raise ValueError("No readable text content extracted from the PDF.")
            
        chunks = ParserService.chunk_text(pages)
        
        # Save record
        db_doc = doc_repo.create({
            "filename": file.filename,
            "storage_path": file_path,
            "checksum": checksum
        })
        
        # Vectorize & Index in ChromaDB
        vector_store_service.add_chunks(db_doc.id, file.filename, chunks)
        
        # Build Knowledge Graph in Neo4j (graceful fallback inside)
        try:
            graph_metrics = graph_builder.build_document_graph(db_doc.id, file.filename, chunks)
            if graph_metrics.get("neo4j_online"):
                logger.info(f"Graph metrics for {file.filename}: {graph_metrics}")
        except Exception as ge:
            logger.warning(f"Knowledge Graph construction failed for {file.filename}: {ge}")

        logger.info(f"Successfully ingested and indexed: {file.filename}")
        return db_doc
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        # Clean up file on disk
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as clean_err:
                logger.error(f"Failed to cleanup file {file_path}: {clean_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}"
        )

@router.get("", response_model=List[Document])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """Lists all ingested documents."""
    return doc_repo.get_multi(skip=skip, limit=limit)

@router.delete("/{document_id}", response_model=Document)
def delete_document(
    document_id: str,
    doc_repo: DocumentRepository = Depends(get_document_repo)
):
    """Deletes document metadata, actual storage file, and vector indexes."""
    db_doc = doc_repo.get(document_id)
    if not db_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
        
    # Remove file on disk
    if os.path.exists(db_doc.storage_path):
        try:
            os.remove(db_doc.storage_path)
        except Exception as e:
            logger.warning(f"Could not remove local file {db_doc.storage_path}: {e}")
            
    # Delete from ChromaDB vector space
    try:
        vector_store_service.delete_document_chunks(document_id)
    except Exception as e:
        logger.warning(f"Could not delete vector embeddings from ChromaDB: {e}")
        
    # Delete from Neo4j Graph Database
    try:
        neo4j_service.delete_document_graph(document_id)
    except Exception as ge:
        logger.warning(f"Could not delete Knowledge Graph entries for document {document_id}: {ge}")

    # Delete from SQLite DB
    return doc_repo.remove(document_id)
