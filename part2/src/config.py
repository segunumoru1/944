import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # Loads variables from .env

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

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Configure Gemini with the correct API key
genai.configure(api_key=settings.GOOGLE_API_KEY)