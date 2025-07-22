from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from auth.dependencies import get_current_user
from models.user import User
from schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse, ResumeUploadCreate, ResumeUploadResponse
from services.user_service import UserService
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    user_service = UserService(db)
    updated_user = user_service.update_user(current_user.id, user_update)
    return updated_user

@router.post("/me/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    resume: ResumeUploadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a resume for the current user. Summary is hardcoded for now."""
    # Simulate ORM insert (replace with actual ORM logic as needed)
    resume_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    summary = "This is a hardcoded summary."
    # Here you would save to DB, e.g. ResumeUpload(...)
    return ResumeUploadResponse(
        id=resume_id,
        user_id=current_user.id,
        file_path=resume.file_path,
        summary=summary,
        uploaded_at=now
    )

def extract_text_from_cv(cv_file: UploadFile) -> str:
    # Placeholder for actual CV text extraction logic
    return f"Extracted text from: {cv_file.filename}"

@router.post("/me/read-cv")
async def read_cv(
    cv: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    cv_data = extract_text_from_cv(cv)
    return {"cv_data": cv_data}

@router.get("/", response_model=List[UserListResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users (paginated)"""
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user (self-deletion only)"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"} 