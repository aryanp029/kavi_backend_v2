from cryptography.fernet import Fernet
import base64
from core.config_loader import settings

def get_fernet_key() -> bytes:
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
    return key

def encrypt_token(token: str) -> str:
    if not token:
        return None
    fernet = Fernet(get_fernet_key())
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return None
    fernet = Fernet(get_fernet_key())
    return fernet.decrypt(encrypted_token.encode()).decode()