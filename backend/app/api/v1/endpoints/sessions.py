from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_session_repo, get_message_repo
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.session import Session, SessionCreate, SessionUpdate, SessionWithMessages
from app.schemas.message import Message

router = APIRouter()

@router.post("", response_model=Session, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: SessionCreate,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """Creates a new conversation session."""
    return session_repo.create(session_in)

@router.get("", response_model=List[Session])
def list_sessions(
    skip: int = 0,
    limit: int = 100,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """Retrieves all sessions sorted by last activity timestamp."""
    return session_repo.get_recent_sessions(skip=skip, limit=limit)

@router.get("/{session_id}", response_model=SessionWithMessages)
def get_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """Fetches a specific session and its full message history."""
    db_session = session_repo.get(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found"
        )
    return db_session

@router.put("/{session_id}", response_model=Session)
def update_session(
    session_id: str,
    session_in: SessionUpdate,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """Updates the properties (e.g., title) of a session."""
    db_session = session_repo.get(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found"
        )
    return session_repo.update(db_session, session_in)

@router.delete("/{session_id}", response_model=Session)
def delete_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """Deletes a session and its associated messages."""
    db_session = session_repo.get(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found"
        )
    return session_repo.remove(session_id)

@router.get("/{session_id}/messages", response_model=List[Message])
def get_session_messages(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo)
):
    """Retrieves messages of a specific session."""
    db_session = session_repo.get(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found"
        )
    return message_repo.get_by_session_id(session_id)
