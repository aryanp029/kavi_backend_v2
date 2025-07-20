from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from core.config_loader import settings
from schemas.oauth import OAuthUserInfo
from models.oauth import OAuthProviderEnum
from auth.jwt import create_access_token, create_refresh_token
from services.oauth_helpers import (
    exchange_code_for_token,
    fetch_user_info,
    upsert_user_and_account
)
from services.user_service import UserService

async def oauth_login(provider: str, code: str, db: Session) -> dict:
    if provider == "google":
        return await _google_oauth_login(code, db)
    elif provider == "linkedin":
        return await _linkedin_oauth_login(code, db)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider")

async def _google_oauth_login(code: str, db: Session) -> dict:
    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://127.0.0.1:8000/api/auth/google/callback",
    }

    token_json = await exchange_code_for_token("https://oauth2.googleapis.com/token", token_data)
    user_data = await fetch_user_info("https://www.googleapis.com/oauth2/v2/userinfo", token_json["access_token"])

    oauth_user_info = OAuthUserInfo(
        email=user_data["email"],
        first_name=user_data.get("given_name"),
        provider_sub=user_data["id"],
        provider=OAuthProviderEnum.GOOGLE
    )

    user = upsert_user_and_account(db, oauth_user_info, token_json)
    
    # Update last login timestamp
    user_service = UserService(db)
    user_service.update_last_login(user.id)
    
    return _create_tokens(user)

async def _linkedin_oauth_login(code: str, db: Session) -> dict:
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://127.0.0.1:8000/api/auth/linkedin/callback",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }

    token_json = await exchange_code_for_token("https://www.linkedin.com/oauth/v2/accessToken", token_data)

    profile_data = await fetch_user_info("https://api.linkedin.com/v2/me", token_json["access_token"])
    email_data = await fetch_user_info("https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))", token_json["access_token"])

    email = email_data["elements"][0]["handle~"]["emailAddress"]
    first_name = profile_data.get("localizedFirstName")

    oauth_user_info = OAuthUserInfo(
        email=email,
        first_name=first_name,
        provider_sub=profile_data["id"],
        provider=OAuthProviderEnum.LINKEDIN
    )

    user = upsert_user_and_account(db, oauth_user_info, token_json)
    
    # Update last login timestamp
    user_service = UserService(db)
    user_service.update_last_login(user.id)
    
    return _create_tokens(user)

def _create_tokens(user) -> dict:
    return {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer"
    }
