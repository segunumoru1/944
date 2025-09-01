import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.models import Base
import os

async def recreate_tables():
    # Get database URL from environment variable or use default
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:password@localhost/insurance_db"
    )
    
    # Create engine and tables
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # Drop tables if they exist (be careful with this in production!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_tables())