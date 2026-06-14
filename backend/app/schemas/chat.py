from pydantic import BaseModel
from typing import List, Optional

class CitationInfo(BaseModel):
    document_id: Optional[str] = None
    filename: str
    page_number: Optional[int] = None
    snippet: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str
    confidence_score: float
    grounding_score: float
    verification_score: float
    verification_status: str
    adaptive_retrieval_used: bool
    verification_improvement: float
    citations: List[CitationInfo] = []
    retrieval_mode: Optional[str] = "vector"
    graph_entities: Optional[List[dict]] = []
    graph_relationships: Optional[List[dict]] = []
    hybrid_used: Optional[bool] = False
    sub_questions: Optional[List[str]] = []
    research_depth: Optional[str] = "shallow"
    retrieval_modes: Optional[List[str]] = []
    faithfulness_score: Optional[float] = 0.0
    answer_relevancy_score: Optional[float] = 0.0

