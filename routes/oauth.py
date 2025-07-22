from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
from core.database import get_db
from core.config_loader import settings
from auth.oauth import oauth_login

router = APIRouter(prefix="/auth", tags=["OAuth"])

@router.get("/google/login")
async def google_login():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": "http://127.0.0.1:8000/api/auth/google/callback",
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    try:
        tokens = await oauth_login("google", code, db)
        frontend_url = f"{settings.FRONTEND_URL}/oauth-success?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
        return RedirectResponse(frontend_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/linkedin/login")
async def linkedin_login():
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": "http://127.0.0.1:8000/api/auth/linkedin/callback",
        "scope": "r_liteprofile r_emailaddress"
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return RedirectResponse(url)

@router.get("/linkedin/callback")
async def linkedin_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    try:
        tokens = await oauth_login("linkedin", code, db)
        frontend_url = f"{settings.FRONTEND_URL}/oauth-success?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
        return RedirectResponse(frontend_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
