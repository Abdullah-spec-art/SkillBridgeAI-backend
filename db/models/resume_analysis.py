import uuid
from typing import Optional
from sqlmodel import Field
from .tablemodel import TableModel

class ResumeAnalysis(TableModel, table=True):
    __tablename__ = "resume_analyses"
    
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    match_percentage: Optional[float] = Field(default=None)
    
    # Storing JSON strings for the MVP before migrating to JSONB columns later
    skill_gaps: Optional[str] = Field(default=None) 
    optimized_json: Optional[str] = Field(default=None)