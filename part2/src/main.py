from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
import base64
from .config import settings
from src.routes import ingest, query, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Database migration function
async def run_database_migrations():
    """Run database migrations on application startup"""
    # Get database credentials from environment variables
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "insurance_db")
    db_user = os.environ.get("DB_USERNAME", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "")
    
    # Check if password needs decoding (optional)
    password_encoded = os.environ.get("DB_PASSWORD_ENCODED", "false").lower() == "true"
    if password_encoded and db_password:
        try:
            db_password = base64.b64decode(db_password).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decode password: {str(e)}")
    
    # Construct database URL
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL)
    
    # Migration statements to add missing columns
    migration_statements = [
        """
        CREATE TABLE IF NOT EXISTS insurance_policies (
            policy_number VARCHAR(255) PRIMARY KEY,
            sum_insured DOUBLE PRECISION,
            premium DOUBLE PRECISION,
            own_retention_ppn DOUBLE PRECISION,
            own_retention_sum_insured DOUBLE PRECISION,
            own_retention_premium DOUBLE PRECISION,
            treaty_retention_ppn DOUBLE PRECISION,
            treaty_sum_insured DOUBLE PRECISION,
            treaty_premium DOUBLE PRECISION,
            insurance_period_start_date DATE,
            insurance_period_end_date DATE,
            vector_id VARCHAR(36)
        )
        """,
        """
        ALTER TABLE insurance_policies 
        ADD COLUMN IF NOT EXISTS insured_name VARCHAR(255)
        """,
        """
        ALTER TABLE insurance_policies 
        ADD COLUMN IF NOT EXISTS facultative_outward_ppn DOUBLE PRECISION
        """,
        """
        ALTER TABLE insurance_policies 
        ADD COLUMN IF NOT EXISTS facultative_outward_sum_insured DOUBLE PRECISION
        """,
        """
        ALTER TABLE insurance_policies 
        ADD COLUMN IF NOT EXISTS facultative_outward_premium DOUBLE PRECISION
        """
    ]
    
    try:
        async with engine.begin() as conn:
            for statement in migration_statements:
                await conn.execute(text(statement))
                logger.info(f"Executed migration: {statement}")
        
        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        # Don't raise the exception - we want the app to start even if migrations fail
    finally:
        await engine.dispose()

app = FastAPI(
    title="Insurance RAG API",
    description="Agentic RAG system for insurance data analysis",
    version="1.0.0"
)

# Register startup event to run migrations
@app.on_event("startup")
async def startup_event():
    logger.info("Running database migrations...")
    await run_database_migrations()
    logger.info("Application startup complete")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = credentials.username == settings.API_USERNAME
    correct_password = credentials.password == settings.API_PASSWORD

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Include routers
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(health.router, prefix="/health", tags=["Health"])

@app.get("/")
async def root():
    return {"message": "Insurance RAG API is running"}