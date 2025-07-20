from pydantic import BaseModel
from models.oauth import OAuthProviderEnum

class OAuthUserInfo(BaseModel):
    email: str
    first_name: str
    provider_sub: str
    provider: OAuthProviderEnum
