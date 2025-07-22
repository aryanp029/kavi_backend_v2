import io
import pymupdf
from linkedin_api.linkedin import Linkedin
from core.config_loader import settings

def extract_text_from_cv(file_bytes: bytes) -> str | None:
    try:
        cv_data = pymupdf.open(stream=io.BytesIO(file_bytes), filetype="pdf")
        full_text = []
        for page_num in range(cv_data.page_count):
            page = cv_data.load_page(page_num)
            page_text = page.get_text("text")
            full_text.append(page_text)
        cv_data.close()
        return "\n".join(full_text)
    except Exception as e:
        return f"Error reading PDF: {e}"

def convert_linkedin_url_to_id(url: str) -> str:
    if url.split("/")[-1] == "":
        linkedin_id = url.split("/")[-2]
    else:
        linkedin_id = url.split("/")[-1]
    return linkedin_id

def linkedin_scrapper(profile_url: str) -> list | str:
    try:
        api = Linkedin(username=settings.LINKEDIN_EMAIL, password=settings.LINKEDIN_PASSWORD)
    except Exception:
        return "Incorrect Credentials"
    user_profile = convert_linkedin_url_to_id(profile_url)
    user_profile = user_profile.split(r"/")[-1]
    profile_data = api.get_profile(user_profile)
    profile_data = list(profile_data.items())
    if len(profile_data) == 0:
        return "Profile does not exist"
    return profile_data 