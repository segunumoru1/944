import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DB_USERNAME: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_PASSWORD: str

    # AI Service API Keys
    GOOGLE_API_KEY: str

    # Pinecone Configuration
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "insurance-rag-index"
    PINECONE_ENV: str = "us-east-1-aws"
    PINECONE_NAMESPACE: str = "insurance_namespace"
    TABLE_NAME: str = "insurance_policies"

    # API Security
    API_USERNAME: str = "admin"
    API_PASSWORD: str = "password"

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
