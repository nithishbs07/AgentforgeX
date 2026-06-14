from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.message import Message

class SessionBase(BaseModel):
    title: str

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    title: Optional[str] = None

class Session(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionWithMessages(Session):
    messages: List[Message] = []

    class Config:
        from_attributes = True
