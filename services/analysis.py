import uuid
from sqlmodel import Session
from db.models.analysis import Analysis
from db.models.user import User
from schemas.analysis import HistoryItemResponse
from services.pdf_parser import ResumeParser
from services.ai_service import SkillGapAnalyzer
import db.repository.analysis as repo
from datetime import datetime

# --- Custom Exceptions ---
class AnalysisNotFoundError(Exception):
    pass

class UnauthorizedAccessError(Exception):
    pass

class InvalidJobDescriptionError(Exception):
    def __init__(self, message): self.message = message

class PDFParsingError(Exception):
    def __init__(self, message): self.message = message

class AIAnalysisError(Exception):
    def __init__(self, message): self.message = message

class FileTypeError(Exception):
    pass

class OutOfScansError(Exception):
    pass

# --- Business Logic ---

def process_and_save_resume(db: Session,current_user: User, user_id: uuid.UUID, file_bytes: bytes, filename: str, content_type: str, job_description: str) -> dict:
    now = datetime.utcnow()
    if current_user.last_replenished_at:
        days_since_refill = (now - current_user.last_replenished_at).days
        if days_since_refill >= 7:
            current_user.scans_remaining = 3
            current_user.last_replenished_at = now
            db.add(current_user)
            db.commit()

    else:
        # First time user setup
        current_user.scans_remaining = 3
        current_user.last_replenished_at = now
        db.add(current_user)
        db.commit()

    if current_user.scans_remaining <= 0:
            raise OutOfScansError("You are out of scans! Your account will be replenished next week.")
    
    if content_type != "application/pdf":
        raise FileTypeError("Only PDF files are accepted.")

    try:
        extracted_text = ResumeParser.extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise PDFParsingError(f"Failed to parse PDF: {str(e)}")

    try:
        ai_result = SkillGapAnalyzer.analyze_resume(resume_text=extracted_text, job_description=job_description)
    except Exception as e:
        raise AIAnalysisError(f"AI Analysis failed: {str(e)}")

    if not ai_result.get("is_valid_jd", True):
        raise InvalidJobDescriptionError(ai_result.get("validation_error", "Invalid job description provided."))

    # Map AI dict directly to SQLModel
    new_analysis = Analysis(
        user_id=user_id,
        job_title=ai_result.get("job_title", "Unknown Role"),
        company=ai_result.get("company", "Unknown Company"),
        resume_filename=filename,
        match_percentage=ai_result.get("match_percentage", 0),
        executive_summary=ai_result.get("executive_summary", ""),
        missing_skills=ai_result.get("missing_skills", []),
        matched_skills=ai_result.get("matched_skills", []),
        partial_skills=ai_result.get("partial_skills", []),
        job_description=job_description,
    )

    db_record = repo.create_analysis(db, new_analysis)
    current_user.scans_remaining -= 1
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Analysis complete and saved!",
        "id": db_record.id,
        "ai_feedback": ai_result,
        "scans_remaining": current_user.scans_remaining
    }

def get_user_analysis_history(db: Session, user_id: uuid.UUID) -> list[HistoryItemResponse]:
    db_analyses = repo.get_all_by_user(db, user_id)
    history_items = []
    
    # Transform raw DB models into lightweight Pydantic schemas for the UI
    for db_item in db_analyses:
        preview_skills = []
        if db_item.missing_skills:
            preview_skills = [
                skill.get("skill") for skill in db_item.missing_skills 
                if isinstance(skill, dict) and "skill" in skill
            ]
        
        history_items.append(HistoryItemResponse(
            id=db_item.id,
            match_percentage=db_item.match_percentage,
            job_title=db_item.job_title,
            company=db_item.company,      
            created_at=db_item.created_at,
            missing_skills_preview=preview_skills,
            resume_filename=db_item.resume_filename
        ))
        
    return history_items

def get_single_analysis(db: Session, analysis_id: uuid.UUID, user_id: uuid.UUID) -> Analysis:
    analysis = repo.get_by_id(db, analysis_id)
    
    if not analysis:
        raise AnalysisNotFoundError("Analysis not found.")
        
    # Ownership Check (Business Logic)
    if analysis.user_id != user_id:
        raise UnauthorizedAccessError("You do not have permission to view this analysis.")
        
    return analysis

def delete_user_analysis(db: Session, analysis_id: uuid.UUID, user_id: uuid.UUID):
    # Reuse the fetch logic so the ownership check happens automatically
    analysis = get_single_analysis(db, analysis_id, user_id)
    repo.delete_analysis(db, analysis)