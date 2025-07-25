import os
from fastapi import UploadFile
from typing import Optional
from utils.linkedin_scrapper import extract_text_from_cv, linkedin_scrapper
from models.resume import Resume
from models.onboarding_summary import OnboardingSummary
from models.user import User
from core.config_loader import settings
from sqlalchemy.orm import Session
from google import genai
from utils import prompts
from datetime import datetime, timezone
from services.onboarding import generate_onboarding_questions_with_gemini

def save_resume_file(file_bytes: bytes, filename: str, user_id: str) -> str:
    static_dir = os.path.join("static", str(user_id))
    os.makedirs(static_dir, exist_ok=True)
    resume_path = os.path.join(static_dir, filename)
    with open(resume_path, "wb") as f:
        f.write(file_bytes)
    return resume_path

def generate_summary_with_gemini(text: str, prompt: str) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY,)  
    response = client.models.generate_content(
    model="gemini-2.5-flash", contents=f"""
    {prompt}
    context:
    {text}""")
    return response.text

def generate_welcome_with_gemini(user_name: str) -> str:
    from google import genai
    from core.config_loader import settings
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = prompts.welcome_prompt.format(user_name=user_name)
    try:
        # print(f"[Gemini] Calling Gemini for user: {user_name}")
        # print(f"[Gemini] Prompt: {prompt}")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        # print(f"[Gemini] Gemini response: {getattr(response, 'text', response)}")
        return response.text
    except Exception as e:
        print(f"[Gemini] Gemini API failed: {e}")
        return f"👋 Hi {user_name}, welcome to the onboarding process! Let's get to know you better."
        
def process_and_save_resume(db: Session, user_id: str, cv_file: Optional[UploadFile], linkedin_profile: Optional[str]) -> Resume:
    resume_path = None
    extracted_text = None
    summary = None
    # Remove all previous resumes for this user to avoid conflicts
    existing_resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    for old_resume in existing_resumes:
        db.delete(old_resume)
    db.commit()
    if cv_file:
        file_bytes = cv_file.file.read()
        resume_path = save_resume_file(file_bytes, cv_file.filename, user_id)
        extracted_text = extract_text_from_cv(file_bytes)
        summary = generate_summary_with_gemini(str(extracted_text), prompts.cv_prompt) if extracted_text else None
    elif linkedin_profile:
        extracted_text = linkedin_scrapper(linkedin_profile)
        summary = generate_summary_with_gemini(str(extracted_text), prompts.linkedin_prompt) if extracted_text else None
    else:
        extracted_text = None
    resume = Resume(user_id=user_id, resume_path=resume_path, linkedin_url=linkedin_profile, summary=summary)
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Add Gemini welcome message to onboarding summary conversation history
    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.first_name if user and user.first_name else "there"
    welcome_msg = generate_welcome_with_gemini(user_name)
    # Generate Gemini onboarding questions
    questions = generate_onboarding_questions_with_gemini()
    question_fields = ["current_work", "reason_for_interview", "where_in_interview_process", "target_company"]
    questions_list = [
        {"bot": questions[field], "field": field} for field in question_fields
    ]
    # Only store the welcome message in conversation_history initially
    conversation_history = [
        {"bot": welcome_msg, "field": "welcome"}
    ]
    onboarding_summary = db.query(OnboardingSummary).filter(OnboardingSummary.user_id == user_id).first()
    if onboarding_summary:
        onboarding_summary.conversation_history = conversation_history
        onboarding_summary.questions = questions_list
        onboarding_summary.updated_at = datetime.now(timezone.utc)
    else:
        onboarding_summary = OnboardingSummary(
            user_id=user_id,
            conversation_history=conversation_history,
            questions=questions_list,
            onboarding_done=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(onboarding_summary)
    db.commit()
    return resume 