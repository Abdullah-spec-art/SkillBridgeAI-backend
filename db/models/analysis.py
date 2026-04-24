from typing import List, Dict, Any
from datetime import datetime
from sqlmodel import Field, Column, JSON
import uuid
from typing import Optional
from db.models.tablemodel import TableModel

class Analysis(TableModel, table=True):
    __tablename__ = 'analysis'
    
    # THE FOREIGN KEY to link back to the user who owns this analysis
    user_id: uuid.UUID = Field(foreign_key="users.id")
    
    #metadata about the job and resume for easy access in the history list
    job_title: Optional[str] = Field(default="Unknown Role")
    company: Optional[str] = Field(default="Unknown Company")
    resume_filename: Optional[str] = Field(default=None) 
    
    # Core AI Analysis
    match_percentage: int
    executive_summary: str
    job_description: str
    
    missing_skills: List[Dict] = Field(default_factory=list, sa_column=Column(JSON))
    matched_skills: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    partial_skills: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Future Roadmap (v2)
    learning_roadmap: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)