from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from core.database import get_db
from models.onboarding_summary import OnboardingSummary
from models.user import User
from services.onboarding import OnboardingChatbot, get_onboarding_summary, CONVERSATION_STATE, get_onboarding_chats
from auth.dependencies import get_current_user
from schemas.onboarding import OnboardingSummaryResponse

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class ChatRequest(BaseModel):
    user_id: UUID
    response: str | None = None

@router.post("/chat")
def onboarding_chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Handle onboarding chat interaction."""
    # Verify user exists
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_name = user.first_name or "there"

    # Get or create chatbot instance
    chatbot = CONVERSATION_STATE.get(req.user_id)
    if not chatbot:
        chatbot = OnboardingChatbot(db, req.user_id, user_name=user_name)
        CONVERSATION_STATE[req.user_id] = chatbot
    # If no response provided, return the first question
    if req.response is None:
        return chatbot.ask_next_question()
    # Process the user's response
    return chatbot.process_response(req.response)

@router.post("/generate_summary")
def generate_onboarding_summary(user_id: UUID, db: Session = Depends(get_db)):
    """Generate and store the onboarding summary for a user based on their resume and conversation history."""
    from google import genai
    from core.config_loader import settings
    from models.onboarding_summary import OnboardingSummary
    from models.resume import Resume
    from utils import prompts
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    onboarding_summary = db.query(OnboardingSummary).filter(OnboardingSummary.user_id == user_id).first()
    if not onboarding_summary:
        raise HTTPException(status_code=404, detail="Onboarding summary not found for this user.")
    # If summary already present and onboarding is done, return it
    if onboarding_summary.onboarding_done and onboarding_summary.summary:
        return {"status": "success", "summary": onboarding_summary.summary}
    # Fetch resume summary
    resume = db.query(Resume).filter(Resume.user_id == user_id).first()
    resume_summary = resume.summary if resume and resume.summary else ""
    # Compose chat history
    chat_pairs = onboarding_summary.conversation_history or []
    print(onboarding_summary.conversation_history)

    chat_text = "\n".join(
        f"Bot: {pair['bot']}\nUser: {pair['user']}" for pair in chat_pairs if 'bot' in pair and 'user' in pair
    )
    # Compose prompt using onboarding_summary_prompt
    prompt = f"{prompts.onboarding_summary_prompt}\n\nResume Summary:\n{resume_summary}\n\nOnboarding Conversation:\n{chat_text}"
    print(prompt)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    summary_text = response.text
    onboarding_summary.summary = summary_text
    db.commit()
    return {"status": "success", "summary": summary_text}

@router.get("/me", response_model=OnboardingSummaryResponse)
def get_my_onboarding_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get onboarding summary for the current authenticated user."""
    summary = db.query(OnboardingSummary).filter(OnboardingSummary.user_id == current_user.id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Onboarding summary not found for this user.")
    return summary

@router.get("/chats")
def get_my_onboarding_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for the current authenticated user as a flat list of role-message dicts."""
    return get_onboarding_chats(db, current_user.id)

@router.delete("/{onboarding_id}", status_code=204)
def delete_onboarding_summary(
    onboarding_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete an onboarding summary by its ID."""
    summary = db.query(OnboardingSummary).filter(OnboardingSummary.id == onboarding_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Onboarding summary not found.")
    db.delete(summary)
    db.commit()
    return None