from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

# --- Execution Log Schemas ---

class ExecutionLogBase(BaseModel):
    log_type: str
    content: str
    tool_name: Optional[str] = None
    data: Optional[dict] = None

class ExecutionLogCreate(ExecutionLogBase):
    analysis_id: UUID

class ExecutionLog(ExecutionLogBase):
    id: UUID
    analysis_id: UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Analysis Schemas ---

class AnalysisBase(BaseModel):
    title: str
    description: Optional[str] = None
    analysis_metadata: Optional[dict] = None

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    analysis_metadata: Optional[dict] = None

class QuestionCreate(BaseModel):
    question: str

class Analysis(AnalysisBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    result: Optional[str] = None
    
    # Optionally include logs in the response
    logs: List[ExecutionLog] = []

    model_config = ConfigDict(from_attributes=True)
