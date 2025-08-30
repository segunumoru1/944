import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import google.generativeai as genai
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DB_USERNAME: Optional[str]
    DB_HOST: Optional[str]
    DB_PORT: Optional[int]
    DB_NAME: Optional[str]
    DB_PASSWORD: Optional[str]
    TABLE_NAME: str = "insurance_policies"

    # AI Service API Keys
    GOOGLE_API_KEY: Optional[str]

    # Pinecone Configuration
    PINECONE_API_KEY: Optional[str]
    PINECONE_INDEX_NAME: str = "insurance-rag-index"
    PINECONE_ENV: str = "us-east-1-aws"
    PINECONE_NAMESPACE: str = "insurance_namespace"

    # API Security
    API_USER: str = "admin"
    API_PASS: str = "changeme"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Configure Gemini only if key present
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
else:
    # Log or raise a friendly runtime error later where LLM is used
    print("WARNING: GOOGLE_API_KEY not set. Gemini calls will fail until provided.")