from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.models import Session as SessionModel

class SessionRepository(BaseRepository[SessionModel]):
    def __init__(self, db: Session):
        super().__init__(SessionModel, db)

    def get_recent_sessions(self, skip: int = 0, limit: int = 100) -> List[SessionModel]:
        """Fetch all sessions ordered by last updated timestamp."""
        statement = select(self.model).order_by(self.model.updated_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())
