from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_session_repo, get_message_repo, get_evaluation_repo
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def query_chat(
    payload: ChatRequest,
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    evaluation_repo: EvaluationRepository = Depends(get_evaluation_repo)
):
    """
    Executes a RAG query for a given active session.
    Retrieves document context, generates an LLM answer, registers citations,
    and stores execution latency performance metrics.
    """
    rag_service = RAGService(
        session_repo=session_repo,
        message_repo=message_repo,
        evaluation_repo=evaluation_repo
    )
    
    try:
        response = rag_service.query_rag(
            session_id=payload.session_id,
            query=payload.message
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred in the RAG execution engine: {str(e)}"
        )
