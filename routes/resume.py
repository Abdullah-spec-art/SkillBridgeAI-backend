from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from db.models.user import User
from db.repository.jwt import get_current_user
from services.pdf_parser import ResumeParser

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    # 1. Validate the file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    # 2. Read the file into memory
    file_bytes = await file.read()
    
    # 3. Extract the text using our new service
    try:
        extracted_text = ResumeParser.extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")
    
    # (Later, we will save this text to the database and send it to the AI)
    
    return {
        "message": "Resume successfully parsed!",
        "user": current_user.email,
        "text_preview": extracted_text[:500] + "..." # Just returning the first 500 chars to test
    }