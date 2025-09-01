import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test_db_connection():
    # Get database credentials from environment variables
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "insurance_db")
    db_user = os.environ.get("DB_USERNAME", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "")
    
    # Construct database URL
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"Testing connection to {db_host}:{db_port}/{db_name} as {db_user}")
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM insurance_policies"))
            count = result.scalar()
            print(f"Connection successful! Found {count} records in insurance_policies table.")
            
            # Test inserting a record
            await conn.execute(
                text("""
                INSERT INTO insurance_policies 
                (policy_number, insured_name, sum_insured, premium)
                VALUES
                ('TEST-POLICY-123', 'Test Insured', 1000000, 50000)
                ON CONFLICT (policy_number) DO UPDATE SET
                insured_name = EXCLUDED.insured_name
                """)
            )
            print("Test record inserted successfully!")
            
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db_connection())