import uuid
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import String, DateTime, JSON, ForeignKey, Text, Boolean
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
    
    # Notebook content (storing ipynb as JSON)
    notebook: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    logs: Mapped[List["AnalysisLog"]] = relationship("AnalysisLog", back_populates="analysis", cascade="all, delete-orphan")
    insights: Mapped[List["Insight"]] = relationship("Insight", back_populates="analysis", cascade="all, delete-orphan")

class AnalysisLog(Base):
    """
    Granular logs for agent execution steps within an analysis.
    Stored in the 'app' schema.
    """
    __tablename__ = "analysis_logs"
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

class DataSource(Base):
    """
    Tracks metadata for data sources (files, WFS, etc.) ingested by the user.
    Stored in the 'app' schema.
    """
    __tablename__ = "data_sources"
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    
    # Table name in DuckDB
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(100), default="main")
    row_count: Mapped[Optional[int]] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Ingestion status: pending, completed, failed
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
    # Source info
    source_type: Mapped[str] = mapped_column(String(50), default="file")  # file, wfs
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    
    # PII detection
    has_pii: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class Insight(Base):
    """
    A single distilled insight extracted from an approved analysis result.
    One row = one bullet point. Stored in the 'app' schema.
    """
    __tablename__ = "insights"
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app.analyses.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_label: Mapped[Optional[str]] = mapped_column(String(255))
    assumptions: Mapped[Optional[str]] = mapped_column(Text)
    limitations: Mapped[Optional[str]] = mapped_column(Text)
    insight_metadata: Mapped[Optional[dict]] = mapped_column(JSON, name="insight_metadata")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="insights")


class SystemSetting(Base):
    """
    Key-value store for application configuration settings.
    Stored in the 'app' schema.
    """
    __tablename__ = "system_settings"
    __table_args__ = {"schema": "app"}

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class KnowledgePage(Base):
    """
    User-created documentation or external integrations representing domain knowledge.
    Stored in the 'app' schema.
    """
    __tablename__ = "knowledge_pages"
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 1. Page Properties (Notion-compatible schema)
    # Includes 'title', 'ownership', and any custom fields
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Standard columns for fast access (mirrored from properties or internal)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Notion-style aesthetics (top-level in Notion Page object)
    icon: Mapped[Optional[dict]] = mapped_column(JSON) # {"type": "emoji", "emoji": "..."}
    cover: Mapped[Optional[dict]] = mapped_column(JSON) # {"type": "external", "external": {"url": "..."}}
    
    # 2. Page Content (List of Notion-style blocks)
    # Each block: {"type": "paragraph", "paragraph": {...}, ...}
    content: Mapped[Optional[List[dict]]] = mapped_column(JSON)
    
    # Meta
    ownership_type: Mapped[str] = mapped_column(String(50), default="individual")
    owner_id: Mapped[Optional[str]] = mapped_column(String(255)) 
    
    # Hierarchy support
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("app.knowledge_pages.id"))
    
    # source tracking
    source: Mapped[str] = mapped_column(String(50), default="manual")
    source_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
