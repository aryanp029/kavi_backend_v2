from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from auth.dependencies import get_current_user
from models.user import User
from models.resume import Resume
from services.resume_service import process_and_save_resume
from core.database import get_db
from uuid import UUID

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/", summary="Upload a resume/CV or provide LinkedIn profile for the current user")
async def upload_resume(
    cv: Optional[UploadFile] = File(None),
    linkedin_profile: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not cv and not linkedin_profile:
        raise HTTPException(status_code=400, detail="Either a resume file or LinkedIn profile must be provided.")
    resume = process_and_save_resume(db, str(current_user.id), cv, linkedin_profile)
    return {
        "id": str(resume.id),
        "resume_path": resume.resume_path,
        "linkedin_url": resume.linkedin_url,
        "summary": resume.summary,
        "uploaded_at": resume.uploaded_at,
    }

@router.get("/", response_model=List[dict], summary="List all resumes with their saved data")
def list_resumes(db: Session = Depends(get_db)):
    resumes = db.query(Resume).all()
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "resume_path": r.resume_path,
            "linkedin_url": r.linkedin_url,
            "summary": r.summary,
            "uploaded_at": r.uploaded_at,
        }
        for r in resumes
    ]

@router.delete("/{resume_id}", status_code=204)
def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a resume by its ID for the current user."""
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    db.delete(resume)
    db.commit()
    return None 