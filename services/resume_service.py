import os
from fastapi import UploadFile
from typing import Optional
from utils.linkedin_scrapper import extract_text_from_cv, linkedin_scrapper
from models.resume import Resume
from core.config_loader import settings
from sqlalchemy.orm import Session
from google import genai
from utils import prompts

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
    return resume 