from pydantic import BaseModel
from typing import List,Optional
import uuid
from datetime import datetime

class MissingSkill(BaseModel):
    skill: str
    reason: str

class AIFeedback(BaseModel):
    match_percentage: int
    executive_summary: str
    job_title: str
    company: str
    missing_skills: List[MissingSkill]
    matched_skills: List[str]  
    partial_skills: List[str]
    is_valid_jd: bool                    
    validation_error: Optional[str] 

# 3. The final response sent to the frontend for the POST /upload route
class AnalysisResponse(BaseModel):
    message: str
    id: uuid.UUID
    ai_feedback: AIFeedback
    scans_remaining: int

# ==========================================
# Future-Proofing: For your GET /history route
# ==========================================
class HistoryItemResponse(BaseModel):
    id: uuid.UUID
    match_percentage: int
    job_title: Optional[str] = "Unknown Role"  
    company: Optional[str] = "Unknown Company"
    created_at: datetime
    missing_skills_preview: List[str] = []
    resume_filename: Optional[str] = None

class HistoryListResponse(BaseModel):
    analyses: List[HistoryItemResponse]