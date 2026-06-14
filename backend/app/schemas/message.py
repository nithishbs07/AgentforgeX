from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.schemas.citation import Citation

class MessageBase(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    session_id: str
    created_at: datetime
    citations: List[Citation] = []

    class Config:
        from_attributes = True
