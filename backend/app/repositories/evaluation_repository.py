from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.repositories.base import BaseRepository
from app.models.models import EvaluationLog

class EvaluationRepository(BaseRepository[EvaluationLog]):
    def __init__(self, db: Session):
        super().__init__(EvaluationLog, db)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Computes aggregate RAG performance statistics:
        - total_queries: Count of logged runs
        - avg_retrieval_time: Mean seconds taken to query vector space
        - avg_generation_time: Mean seconds taken for LLM calls
        - avg_top_score: Mean similarity score of top retrieval chunks
        - avg_avg_score: Mean of average similarity scores per run
        """
        statement = select(
            func.count(self.model.id).label("total_queries"),
            func.avg(self.model.retrieval_time).label("avg_retrieval_time"),
            func.avg(self.model.generation_time).label("avg_generation_time"),
            func.avg(self.model.top_score).label("avg_top_score"),
            func.avg(self.model.avg_score).label("avg_avg_score")
        )
        
        result = self.db.execute(statement).first()
        if not result or result.total_queries == 0:
            return {
                "total_queries": 0,
                "avg_retrieval_time": 0.0,
                "avg_generation_time": 0.0,
                "avg_top_score": 0.0,
                "avg_avg_score": 0.0
            }
            
        return {
            "total_queries": int(result.total_queries),
            "avg_retrieval_time": float(result.avg_retrieval_time or 0.0),
            "avg_generation_time": float(result.avg_generation_time or 0.0),
            "avg_top_score": float(result.avg_top_score or 0.0),
            "avg_avg_score": float(result.avg_avg_score or 0.0)
        }
