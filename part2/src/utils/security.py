import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from src.config import settings
import logging
import re

logger = logging.getLogger(__name__)

security = HTTPBasic()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def _is_bcrypt_hash(s: str) -> bool:
    """Detect whether a string looks like a bcrypt hash"""
    return isinstance(s, str) and s.startswith("$2")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash or plain-text fallback.

    - If `hashed_password` is a bcrypt hash, use bcrypt.checkpw.
    - Otherwise compare plain text (useful for env-stored plaintext during development).
    """
    if not hashed_password:
        return False

    try:
        if _is_bcrypt_hash(hashed_password):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        # fallback: direct string compare (handles plaintext stored in .env)
        return plain_password == hashed_password
    except ValueError:
        # invalid salt or malformed hash
        logger.exception("Malformed hashed password encountered during verification.")
        return False

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic authentication credentials"""
    correct_username = credentials.username == settings.API_USERNAME
    correct_password = verify_password(credentials.password, settings.API_PASSWORD)

    if not (correct_username and correct_password):
        logger.warning(f"Failed authentication attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

def sanitize_sql_input(input_string: str) -> str:
    """Sanitize input to prevent SQL injection"""
    if not input_string:
        return ""
    
    # Remove SQL keywords and special characters
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION", "OR", "AND"]
    sanitized = input_string
    for keyword in sql_keywords:
        sanitized = sanitized.replace(keyword, "")
        sanitized = sanitized.replace(keyword.lower(), "")
    
    # Remove special characters
    sanitized = re.sub(r'[;\\\'"<>%$]', '', sanitized)
    
    return sanitized

def validate_api_key(api_key: str) -> bool:
    """Validate API key (for future use with API key authentication)"""
    # This is a placeholder for API key validation
    # In a production system, you would check against a database of valid keys
    return api_key == settings.GOOGLE_API_KEY  # Using Gemini key as example