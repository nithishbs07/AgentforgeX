from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.models import Document as DocumentModel

class DocumentRepository(BaseRepository[DocumentModel]):
    def __init__(self, db: Session):
        super().__init__(DocumentModel, db)

    def get_by_checksum(self, checksum: str) -> Optional[DocumentModel]:
        """Look up document by checksum to avoid duplicate ingestion."""
        statement = select(self.model).filter(self.model.checksum == checksum)
        return self.db.scalars(statement).first()
