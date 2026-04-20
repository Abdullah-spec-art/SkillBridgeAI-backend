import uuid

from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlmodel import Session # NEW: Import Session
from db.models.user import User
from db.repository.jwt import get_current_user

# You likely have a file that generates your database session (e.g., db/database.py or db/session.py)
from db.database import get_session # NEW: Adjust this import to match where your get_session function lives!

from services.pdf_parser import ResumeParser
from services.ai_service import SkillGapAnalyzer
from db.repository.analysis import AnalysisRepository,get_analysis_for_user, get_analysis_by_id, get_analysis_by_id, delete_analysis_by_id

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload")
async def upload_resume(
    job_description: str = Form(...), 
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session) 
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    file_bytes = await file.read()
    
    try:
        extracted_text = ResumeParser.extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")
        
    try:
        # 1. Get the JSON from Gemini
        analysis_result = SkillGapAnalyzer.analyze_resume(
            resume_text=extracted_text, 
            job_description=job_description
        )
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"AI Analysis failed: {str(e)}")
         
    try:
        # 2. NEW: Save it permanently to PostgreSQL!
        AnalysisRepository.save_analysis(
            session=session,
            user_id=current_user.id,
            job_description=job_description,
            ai_result=analysis_result
        )
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to save to database: {str(e)}")
    
    # 3. Return it to the user
    return {
        "message": "Analysis complete and saved!",
        "user": current_user.email,
        "ai_feedback": analysis_result
    }

@router.get("/my-analysis")
def get_my_analyses(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        analyses = get_analysis_for_user(session=session, user_id=current_user.id)
        return {"analyses": analyses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analyses: {str(e)}")


@router.get("/analysis/{analysis_id}")
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    analysis = get_analysis_by_id(session=session, analysis_id=analysis_id,user_id=current_user.id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"analysis": analysis}


@router.delete("/analysis/{analysis_id}")
def delete_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    success =delete_analysis_by_id(session=session, analysis_id=analysis_id,user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis not found or could not be deleted")
    return {"message": "Analysis deleted successfully"}