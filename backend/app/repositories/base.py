from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Base class for data access repository pattern.
        """
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return self.db.get(self.model, id)

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch multiple records with pagination."""
        statement = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())

    def create(self, obj_in: Any) -> ModelType:
        """Create a new record in the database."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        elif hasattr(obj_in, "model_dump"):
            db_obj = self.model(**obj_in.model_dump())
        else:
            db_obj = obj_in
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: Any) -> ModelType:
        """Update fields of an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: Any) -> Optional[ModelType]:
        """Remove a record by primary key."""
        obj = self.db.get(self.model, id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
