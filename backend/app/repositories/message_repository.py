from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.models import Message as MessageModel

class MessageRepository(BaseRepository[MessageModel]):
    def __init__(self, db: Session):
        super().__init__(MessageModel, db)

    def get_by_session_id(self, session_id: str) -> List[MessageModel]:
        """Fetch all messages for a session ordered by creation time."""
        statement = (
            select(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(self.model.created_at.asc())
        )
        return list(self.db.scalars(statement).all())
