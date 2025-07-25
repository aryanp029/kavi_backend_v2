from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class OnboardingSummaryResponse(BaseModel):
    id: UUID
    user_id: UUID
    current_work: Optional[str]
    reason_for_interview: Optional[str]
    where_in_interview_process: Optional[str]
    target_company: Optional[str]
    onboarding_done: bool
    conversation_history: Optional[list]
    questions: Optional[list]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
