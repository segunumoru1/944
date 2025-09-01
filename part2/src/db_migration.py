from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/insurance_db")

async def run_migration():
    # Create async engine
    engine = create_async_engine(DATABASE_URL)
    
    # Migration statements to add missing columns
    migration_statements = [
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
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())