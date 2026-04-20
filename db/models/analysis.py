from typing import List, Dict, Any
from datetime import datetime
from sqlmodel import Field, Column, JSON
import uuid
from db.models.tablemodel import TableModel

class Analysis(TableModel, table=True):
    __tablename__ = 'analyses'
    
    # THE FOREIGN KEY: Ties this row to the User
    user_id: uuid.UUID = Field(foreign_key="users.id")
    
    # The Inputs
    job_description: str
    
    # The AI Outputs
    match_percentage: int
    executive_summary: str
    
    # The JSON array of missing skills
    missing_skills: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)