import httpx
from sqlalchemy.orm import Session
from models.user import User
from models.oauth import OAuthAccount, OAuthProviderEnum
from core.security import encrypt_token
from schemas.oauth import OAuthUserInfo
from datetime import datetime, timedelta


async def exchange_code_for_token(token_url: str, data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = await client.post(token_url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()


async def fetch_user_info(userinfo_url: str, access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = await client.get(userinfo_url, headers=headers)
        response.raise_for_status()
        return response.json()


def upsert_user_and_account(db: Session, user_info: OAuthUserInfo, token_data: dict) -> User:
    # 1. Lookup or create user
    user = db.query(User).filter_by(email=user_info.email).first()
    if not user:
        user = User(email=user_info.email, first_name=user_info.first_name)
        db.add(user)
        db.flush()  # to get user.id before committing

    # 2. Lookup or create oauth account
    oauth_account = db.query(OAuthAccount).filter_by(
        provider=user_info.provider,
        provider_sub=user_info.provider_sub
    ).first()

    if not oauth_account:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=user_info.provider,
            provider_sub=user_info.provider_sub,
        )
        db.add(oauth_account)

    # 3. Update token fields
    oauth_account.access_token_enc = encrypt_token(token_data.get("access_token"))
    oauth_account.refresh_token_enc = encrypt_token(token_data.get("refresh_token", ""))
    
    expires_in = token_data.get("expires_in")
    if expires_in:
        oauth_account.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))

    db.commit()
    return user
