import os
from google import genai
from google.genai import types
from core.config_loader import settings
import json
from services.onboarding import generate_onboarding_questions_with_gemini
def generate_questions_with_gemini():
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
    return response.text

# if __name__ == "__main__":
#     response = generate_questions_with_gemini()
#     print(response)
#     questions = json.loads(response)
#     print(questions)

print(generate_onboarding_questions_with_gemini())