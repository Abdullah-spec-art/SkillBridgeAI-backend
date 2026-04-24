import uuid
from alembic.util import status
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlmodel import Session

from db.models.user import User
from db.repository.jwt import get_current_user
from db.database import get_session
from schemas.analysis import AnalysisResponse, HistoryListResponse

# Import the service module
import services.analysis as AnalysisService

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/upload-resume", response_model=AnalysisResponse)
async def upload_resume(
    job_description: str = Form(...), 
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session) 
):
    file_bytes = await file.read()
    
    try:
        return AnalysisService.process_and_save_resume(
            db=session,
            current_user=current_user,
            user_id=current_user.id,
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            job_description=job_description
        )
    except AnalysisService.OutOfScansError as e:
            raise HTTPException(status_code=403, detail=str(e))
    except AnalysisService.FileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnalysisService.InvalidJobDescriptionError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except AnalysisService.PDFParsingError as e:
        raise HTTPException(status_code=500, detail=e.message)
    except AnalysisService.AIAnalysisError as e:
        # --- Check if it's our specific rate limit error ---
        if "RATE_LIMIT_EXCEEDED" in e.message:
            raise HTTPException(
                status_code=429,  
                detail="The AI engine is currently at maximum capacity. Please wait 60 seconds and try again."
            )
        # Otherwise, throw the normal 500 error
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("", response_model=HistoryListResponse)
def get_my_analyses(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        history_items = AnalysisService.get_user_analysis_history(db=session, user_id=current_user.id)
        return HistoryListResponse(analyses=history_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis history.")

@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        analysis = AnalysisService.get_single_analysis(db=session, analysis_id=analysis_id, user_id=current_user.id)
        return {"analysis": analysis}
    except AnalysisService.AnalysisNotFoundError:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    except AnalysisService.UnauthorizedAccessError:
        raise HTTPException(status_code=403, detail="Access denied.")

@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        AnalysisService.delete_user_analysis(db=session, analysis_id=analysis_id, user_id=current_user.id)
        return {"message": "Analysis deleted successfully"}
    except AnalysisService.AnalysisNotFoundError:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    except AnalysisService.UnauthorizedAccessError:
        raise HTTPException(status_code=403, detail="Access denied.")