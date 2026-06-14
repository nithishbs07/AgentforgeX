from pydantic import BaseModel
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    storage_path: str
    checksum: str

class Document(DocumentBase):
    id: str
    storage_path: str
    checksum: str
    created_at: datetime

    class Config:
        from_attributes = True
