from pydantic import BaseModel
from typing import Optional

class CitationBase(BaseModel):
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    snippet: str

class CitationCreate(CitationBase):
    message_id: str

class Citation(CitationBase):
    id: str
    message_id: str
    filename: Optional[str] = None
    
    class Config:
        from_attributes = True

