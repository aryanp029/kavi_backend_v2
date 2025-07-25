from sqlalchemy.orm import Session
from typing import Dict, Optional
import random
from uuid import UUID
from datetime import datetime, timezone
from models.onboarding_summary import OnboardingSummary
from google import genai
from core.config_loader import settings
import json
from google.genai import types

# Remove static QUESTION_TEMPLATES and random choice logic
# QUESTION_TEMPLATES = {...}
# In-memory store for conversation state (replace with database/redis for production)
CONVERSATION_STATE: Dict[UUID, "OnboardingChatbot"] = {}
CONVERSATION_QUESTIONS: Dict[UUID, list] = {}  # Store generated questions per user

def generate_onboarding_questions_with_gemini() -> dict:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    onboarding_question_prompt = """
    Create four concise and completely distinct questions for a user's interview prep, each targeting a specific field:
    1. current_work, 2. reason_for_interview, 3. where_in_interview_process, and 4. target_company.
    Each question must:
    Be warm, conversational, and supportive.
    Be exactly one sentence or max 20-30 words.
    Be substantially different in phrasing, word choice, and sentence structure — no two questions should sound remotely alike.
    Avoid repeating sentence patterns or openings (e.g., no “What’s your…” or “Are you…” across multiple questions).
    Each question should sound natural and tailored only to its specific field.
    Field-specific constraints:
    current_work: Ask about the user’s current role and how long they’ve been in it — don’t reference resumes or LinkedIn.
    reason_for_interview: Ask what’s prompting their prep — include varied examples like switching jobs, growing confidence, or aiming high.
    where_in_interview_process: Ask where they are in the process — include options like just getting started, mid-process, final rounds, or skill-building.
    target_company: Ask about any company or role they’re aiming for — offer the choice to share a job description or say they’re exploring.
    Return the result as a JSON object with keys 'current_work', 'reason_for_interview', 'where_in_interview_process', and 'target_company', each containing one question.
    Return ONLY the JSON object with no additional text.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=onboarding_question_prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            temperature=1.2,
            response_schema={
                "type": "object",
                "properties": {
                    "current_work": {"type": "string"},
                    "reason_for_interview": {"type": "string"},
                    "where_in_interview_process": {"type": "string"},
                    "target_company": {"type": "string"},
                },
                "required": [
                    "current_work",
                    "reason_for_interview",
                    "where_in_interview_process",
                    "target_company"
                ]
            }
        ),
    )

    # Parse the JSON from Gemini's response
    try:
        questions = json.loads(response.text)
        print(questions)
    except Exception:
        # fallback to default questions if parsing fails
        questions = {
            "current_work": "What is your current work or role?",
            "reason_for_interview": "What is your main reason for seeking a new interview?",
            "where_in_interview_process": "Where are you in the interview process?",
            "target_company": "Which company are you targeting for your next role?"
        }
    return questions

def validate_response(field: str, response: str) -> bool:
    """Validate if the response is non-empty and reasonable for the field."""
    if not response or len(response.strip()) < 2:
        return False
    return True

class OnboardingChatbot:
    def __init__(self, db_session: Session, user_id: UUID, user_name: str = "there"):
        self.db_session = db_session
        self.user_id = user_id
        self.user_name = user_name
        self.fields = ["current_work", "reason_for_interview", "where_in_interview_process", "target_company"]
        self.responses: Dict[str, Optional[str]] = {field: None for field in self.fields}
        self.max_retries = 3
        self.current_field_index = 0
        self.retries = 0
        self.welcomed = False
        self.last_bot_message = None
        # Load conversation_history and questions from DB if present
        existing_summary = db_session.query(OnboardingSummary).filter(OnboardingSummary.user_id == user_id).first()
        if existing_summary:
            self.conversation_history = existing_summary.conversation_history or []
            self.questions = existing_summary.questions or []
        else:
            self.conversation_history = []
            self.questions = []
        # If onboarding is already done, load responses
        if existing_summary and existing_summary.onboarding_done:
            self.responses = {
                "current_work": existing_summary.current_work,
                "reason_for_interview": existing_summary.reason_for_interview,
                "where_in_interview_process": existing_summary.where_in_interview_process,
                "target_company": existing_summary.target_company
            }
            self.current_field_index = len(self.fields)
            self.welcomed = True

    def get_welcome_message(self):
        # You can add more rephrased welcome templates here
        templates = [
            f"👋 Hi {self.user_name}, welcome to the onboarding process! Let's get to know you better.",
            f"Hello {self.user_name}! Ready to start your onboarding journey?",
            f"Welcome {self.user_name}! I'll ask you a few questions to get started.",
        ]
        return random.choice(templates)

    def ask_next_question(self) -> dict:
        # Find the first unanswered entry (including welcome)
        for entry in self.conversation_history:
            if "user" not in entry:
                self.last_bot_message = entry["bot"]
                field = entry["field"]
                return {
                    "status": "question",
                    "message": self.last_bot_message,
                    "field": field
                }
        # If all in conversation_history are answered, check questions for next
        existing_summary = self.db_session.query(OnboardingSummary).filter(OnboardingSummary.user_id == self.user_id).first()
        if existing_summary and existing_summary.questions:
            # Find the next question not yet in conversation_history
            asked_fields = {entry["field"] for entry in self.conversation_history}
            for q in existing_summary.questions:
                if q["field"] not in asked_fields:
                    self.conversation_history.append({"bot": q["bot"], "field": q["field"]})
                    existing_summary.conversation_history = self.conversation_history
                    self.db_session.commit()
                    self.last_bot_message = q["bot"]
                    return {
                        "status": "question",
                        "message": q["bot"],
                        "field": q["field"]
                    }
        return self.complete_onboarding()

    def process_response(self, response: str) -> dict:
        # Find the first unanswered entry (including welcome)
        for entry in self.conversation_history:
            if "user" not in entry:
                field = entry["field"]
                entry["user"] = response
                self.responses[field] = response
                # Persist conversation history and update DB field if not welcome
                existing_summary = self.db_session.query(OnboardingSummary).filter(OnboardingSummary.user_id == self.user_id).first()
                if existing_summary:
                    existing_summary.conversation_history = self.conversation_history
                    if field != "welcome":
                        setattr(existing_summary, field, response)
                    existing_summary.updated_at = datetime.now(timezone.utc)
                    self.db_session.commit()
                else:
                    onboarding_summary = OnboardingSummary(
                        user_id=self.user_id,
                        onboarding_done=False,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        conversation_history=self.conversation_history
                    )
                    if field != "welcome":
                        setattr(onboarding_summary, field, response)
                    self.db_session.add(onboarding_summary)
                    self.db_session.commit()
                break
        # After answering, ask next question (which will append it to history if needed)
        return self.ask_next_question()

    def complete_onboarding(self) -> dict:
        if all(self.responses[field] for field in self.fields):
            existing_summary = self.db_session.query(OnboardingSummary).filter(OnboardingSummary.user_id == self.user_id).first()
            if existing_summary:
                existing_summary.current_work = self.responses["current_work"]
                existing_summary.reason_for_interview = self.responses["reason_for_interview"]
                existing_summary.where_in_interview_process = self.responses["where_in_interview_process"]
                existing_summary.target_company = self.responses["target_company"]
                existing_summary.onboarding_done = True
                existing_summary.updated_at = datetime.now(timezone.utc)
                existing_summary.conversation_history = self.conversation_history
            else:
                onboarding_summary = OnboardingSummary(
                    user_id=self.user_id,
                    current_work=self.responses["current_work"],
                    reason_for_interview=self.responses["reason_for_interview"],
                    where_in_interview_process=self.responses["where_in_interview_process"],
                    target_company=self.responses["target_company"],
                    onboarding_done=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    conversation_history=self.conversation_history
                )
                self.db_session.add(onboarding_summary)
            self.db_session.commit()
            CONVERSATION_STATE.pop(self.user_id, None)
            return {
                "status": "complete",
                "message": (
                    "--- Summary Complete ---\n"
                    f"Current Work: {self.responses['current_work']}\n"
                    f"Reason: {self.responses['reason_for_interview']}\n"
                    f"Process Stage: {self.responses['where_in_interview_process']}\n"
                    f"Target Company: {self.responses['target_company']}\n"
                    f"Onboarding Done: True"
                ),
                "conversation_history": self.conversation_history
            }
        else:
            for i, field in enumerate(self.fields):
                if not self.responses[field]:
                    self.current_field_index = i
                    self.retries = 0
                    return {
                        "status": "question",
                        "message": self.conversation_history[self.current_field_index + 1]["bot"], # Use dynamic question
                        "field": field
                    }

    def get_flat_chat_history(self):
        """Return the chat history as a flat list of role-message dicts for frontend display."""
        flat = []
        for pair in self.conversation_history:
            if 'bot' in pair:
                flat.append({"role": "bot", "message": pair["bot"]})
            if 'user' in pair:
                flat.append({"role": "user", "message": pair["user"]})
        return flat

def get_onboarding_summary(db: Session, user_id: UUID) -> dict:
    summary = db.query(OnboardingSummary).filter(OnboardingSummary.user_id == user_id).first()
    if not summary:
        return {"status": "error", "message": "No onboarding summary found for this user."}
    did_chat = any([
        summary.current_work,
        summary.reason_for_interview,
        summary.where_in_interview_process,
        summary.target_company
    ])
    return {
        "status": "success",
        "summary": {
            "id": summary.id,
            "user_id": summary.user_id,
            "current_work": summary.current_work,
            "reason_for_interview": summary.reason_for_interview,
            "where_in_interview_process": summary.where_in_interview_process,
            "target_company": summary.target_company,
            "onboarding_done": summary.onboarding_done,
            "created_at": summary.created_at,
            "updated_at": summary.updated_at,
            "did_chat": did_chat,
            "conversation_history": summary.conversation_history or []
        }
    }

def get_onboarding_chats(db: Session, user_id: UUID):
    """Get chat history for a user as a flat list of role-message dicts."""
    summary = db.query(OnboardingSummary).filter(OnboardingSummary.user_id == user_id).first()
    if not summary or not summary.conversation_history:
        return []
    flat = []
    for pair in summary.conversation_history:
        if 'bot' in pair:
            flat.append({"role": "bot", "message": pair["bot"]})
        if 'user' in pair:
            flat.append({"role": "user", "message": pair["user"]})
    return flat