from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

# --- Analysis Log Schemas ---

class AnalysisLogBase(BaseModel):
    log_type: str
    content: str
    tool_name: Optional[str] = None
    data: Optional[dict] = None

class AnalysisLogCreate(AnalysisLogBase):
    analysis_id: UUID

class AnalysisLog(AnalysisLogBase):
    id: UUID
    analysis_id: UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Analysis Schemas ---

class AnalysisBase(BaseModel):
    title: str
    description: Optional[str] = None
    analysis_metadata: Optional[dict] = None
    notebook: Optional[dict] = None

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    analysis_metadata: Optional[dict] = None
    notebook: Optional[dict] = None

class QuestionCreate(BaseModel):
    question: str

class Analysis(AnalysisBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    result: Optional[str] = None
    
    # Optionally include logs in the response
    logs: List[AnalysisLog] = []

    model_config = ConfigDict(from_attributes=True)

class QuickInsightResponse(BaseModel):
    analysis_id: UUID
    title: str
    summary: str
    stats: dict
    followup_questions: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class QuickInsightExistingRequest(BaseModel):
    file_id: UUID

# --- Insight Schemas ---

class InsightBase(BaseModel):
    content: str
    source_label: Optional[str] = None
    assumptions: Optional[str] = None
    limitations: Optional[str] = None
    insight_metadata: Optional[dict] = None

class Insight(InsightBase):
    id: UUID
    analysis_id: UUID
    is_verified: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InsightStats(BaseModel):
    verified_count: int
    analyses_count: int
    contributors_count: int

# --- User Schemas ---

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Data Source Schemas ---

class DataSourceBase(BaseModel):
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int
    table_name: str
    schema_name: str = "main"
    row_count: Optional[int] = None
    description: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    file_hash: Optional[str] = None
    source_type: str = "file"
    source_url: Optional[str] = None
    has_pii: bool = False
    owner_id: Optional[UUID] = None

class DataSource(DataSourceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_duplicate: bool = False
    
    # Optional nested owner for detail views
    owner: Optional[User] = None

    model_config = ConfigDict(from_attributes=True)

class DataSourceUpdate(BaseModel):
    description: Optional[str] = None

class DataSourcePIIUpdate(BaseModel):
    has_pii: bool

# --- WFS Schemas ---

class WFSLayer(BaseModel):
    name: str
    title: str
    formats: List[str]

class WFSInjestRequest(BaseModel):
    url: str
    layer: Optional[str] = None


# --- Setting Schemas ---

class SystemSettingBase(BaseModel):
    key: str
    value: dict

class SystemSetting(SystemSettingBase):
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# --- Knowledge Page Schemas ---

class KnowledgePageBase(BaseModel):
    title: str
    properties: Optional[dict] = {}
    content: Optional[List[dict]] = None
    icon: Optional[dict] = None
    cover: Optional[dict] = None
    ownership_type: str = "individual"
    owner_id: Optional[str] = None
    parent_id: Optional[UUID] = None
    source: str = "manual"
    source_id: Optional[str] = None

    @field_validator('properties', 'icon', 'cover', 'content', mode='before')
    @classmethod
    def ensure_not_none(cls, v):
        if v is None:
            # Return appropriate default for each type
            # (In practice, properties is usually a dict, content is a list)
            return {} if isinstance(v, dict) or v is None else v
        return v

    # Simplified version just for properties to be safe
    @field_validator('properties', mode='before')
    @classmethod
    def validate_properties(cls, v):
        return v if v is not None else {}

class KnowledgePageCreate(KnowledgePageBase):
    pass

class KnowledgePageUpdate(BaseModel):
    title: Optional[str] = None
    properties: Optional[dict] = None
    content: Optional[List[dict]] = None
    icon: Optional[dict] = None
    cover: Optional[dict] = None
    ownership_type: Optional[str] = None
    owner_id: Optional[str] = None
    parent_id: Optional[UUID] = None

class KnowledgePage(KnowledgePageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
