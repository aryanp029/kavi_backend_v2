from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from core.database import get_db
from models.onboarding_summary import OnboardingSummary
from models.user import User

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])

@router.post("/chat",)
def onboarding_chat(req, db: Session = Depends(get_db)):
   pass
   

@router.post("/generate_summary")
def generate_onboarding_summary(user_id: UUID, db: Session = Depends(get_db)):
   pass