from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.evaluation_repository import EvaluationRepository

def get_session_repo(db: Session = Depends(get_db)) -> SessionRepository:
    """Injects SessionRepository instance initialized with database session."""
    return SessionRepository(db)

def get_message_repo(db: Session = Depends(get_db)) -> MessageRepository:
    """Injects MessageRepository instance initialized with database session."""
    return MessageRepository(db)

def get_document_repo(db: Session = Depends(get_db)) -> DocumentRepository:
    """Injects DocumentRepository instance initialized with database session."""
    return DocumentRepository(db)

def get_evaluation_repo(db: Session = Depends(get_db)) -> EvaluationRepository:
    """Injects EvaluationRepository instance initialized with database session."""
    return EvaluationRepository(db)
