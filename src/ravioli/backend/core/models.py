import uuid
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ravioli.backend.core.database import Base

class Analysis(Base):
    """
    Represents a high-level goal or task given to an agent.
    Stored in the 'app' schema.
    """
    __tablename__ = "analyses"
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Final result or summary
    result: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata for the analysis (e.g., config, parameters)
    analysis_metadata: Mapped[Optional[dict]] = mapped_column(JSON, name="analysis_metadata")

    # Relationships
    logs: Mapped[List["ExecutionLog"]] = relationship("ExecutionLog", back_populates="analysis", cascade="all, delete-orphan")

class ExecutionLog(Base):
    """
    Granular logs for agent execution steps within an analysis.
    Stored in the 'app' schema.
    """
    __tablename__ = "execution_logs"
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app.analyses.id"), nullable=False)
    
    # What was happening? (thought, tool_use, observation, error)
    log_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Content of the log
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Optional tool name if log_type is tool_use
    tool_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Structured data if needed
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="logs")
