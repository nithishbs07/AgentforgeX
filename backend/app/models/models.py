import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    # Python 3.12 compliant timezone-naive UTC datetime
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    citations: Mapped[List["Citation"]] = relationship(
        "Citation", back_populates="message", cascade="all, delete-orphan", passive_deletes=True
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

    # Relationships
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="document")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="citations")
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="citations")

    @property
    def filename(self) -> str:
        return self.document.filename if self.document else "Unknown Document"



class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_chunks: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized string
    retrieved_count: Mapped[int] = mapped_column(Integer, nullable=False)
    top_score: Mapped[float] = mapped_column(Float, nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, nullable=False)
    retrieval_time: Mapped[float] = mapped_column(Float, nullable=False)
    generation_time: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    execution_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON serialized string
    verification_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    grounding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adaptive_retrieval_used: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    retrieval_attempts: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    evidence_expansion_factor: Mapped[Optional[float]] = mapped_column(Float, default=1.0)
    verification_improvement: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    planner_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    research_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aggregation_latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sub_question_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    research_depth: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    faithfulness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    answer_relevancy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)



