import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, create_engine
import pandas as pd
import logging
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_database():
    # Get DB credentials from environment or use defaults from your .env
    DB_HOST = os.environ.get("DB_HOST", "138.197.129.114")
    DB_PORT = os.environ.get("DB_PORT", "5476")
    DB_NAME = os.environ.get("DB_NAME", "insurance_db")
    DB_USERNAME = os.environ.get("DB_USERNAME", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "XlxKtnW8NRVSIEHC3CzKihPQRATGIsqo0525SORi265JeZdSs1RakwwzZAyM3W9E")

    # Create both sync and async engines for different operations
    db_url = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    async_engine = create_async_engine(db_url)
    
    try:
        # Check if table exists and create if needed
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS insurance_policies (
            policy_number VARCHAR(255) PRIMARY KEY,
            insured_name VARCHAR(255),
            sum_insured DOUBLE PRECISION,
            premium DOUBLE PRECISION,
            own_retention_ppn DOUBLE PRECISION,
            own_retention_sum_insured DOUBLE PRECISION,
            own_retention_premium DOUBLE PRECISION,
            treaty_ppn DOUBLE PRECISION,
            treaty_sum_insured DOUBLE PRECISION,
            treaty_premium DOUBLE PRECISION,
            facultative_outward_ppn DOUBLE PRECISION,
            facultative_outward_sum_insured DOUBLE PRECISION,
            facultative_outward_premium DOUBLE PRECISION,
            insurance_period_start_date TIMESTAMP,
            insurance_period_end_date TIMESTAMP,
            vector_id VARCHAR(36)
        )
        """
        
        async with async_engine.begin() as conn:
            await conn.execute(text(create_table_sql))
            logger.info("Verified insurance_policies table exists or created it")
            
            # Check for column naming issues
            check_columns = """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'insurance_policies'
            """
            result = await conn.execute(text(check_columns))
            columns = [row[0] for row in result.all()]
            logger.info(f"Current columns: {columns}")
            
            # Fix treaty_ppn vs treaty_retention_ppn naming issue if needed
            if 'treaty_retention_ppn' in columns and 'treaty_ppn' not in columns:
                await conn.execute(text("ALTER TABLE insurance_policies RENAME COLUMN treaty_retention_ppn TO treaty_ppn"))
                logger.info("Renamed treaty_retention_ppn to treaty_ppn")
            elif 'treaty_ppn' in columns and 'treaty_retention_ppn' not in columns:
                logger.info("Column treaty_ppn already exists")
            
            # Count existing records
            count_result = await conn.execute(text("SELECT COUNT(*) FROM insurance_policies"))
            record_count = count_result.scalar()
            logger.info(f"Current record count: {record_count}")
            
        # If no data in database, let's load sample data
        if record_count == 0:
            logger.info("No records found, attempting to load sample data...")
            
            # Try to find your sample Excel file
            import glob
            sample_files = glob.glob("**/*.xlsx", recursive=True)
            
            if sample_files:
                # Load first Excel file found
                sample_file = sample_files[0]
                logger.info(f"Loading sample data from {sample_file}")
                
                # Load Excel data directly into database
                df = pd.read_excel(sample_file)
                
                # Print original columns for debugging
                logger.info(f"Original Excel columns: {df.columns.tolist()}")
                
                # Check if column mapping is needed
                column_mapping = {
                    "INSURED": "insured_name",
                    "POLICY NUMBER": "policy_number",
                    "SUM INSURED": "sum_insured",
                    "PREMIUM": "premium",
                    "OWN RETENTION PPN": "own_retention_ppn",
                    "OWN RETENTION SUM INSURED": "own_retention_sum_insured",
                    "OWN RETENTION PREMIUM": "own_retention_premium",
                    "TREATY PPN": "treaty_ppn",
                    "TREATY SUM INSURED": "treaty_sum_insured",
                    "TREATY PREMIUM": "treaty_premium",
                    "FACULTATIVE OUTWARD PPN": "facultative_outward_ppn",
                    "FACULTATIVE OUTWARD SUM INSURED": "facultative_outward_sum_insured",
                    "FACULTATIVE OUTWARD PREMIUM": "facultative_outward_premium",
                    "PERIOD OF INSURANCE": "insurance_period"
                }
                
                # Rename only columns that exist
                rename_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
                df.rename(columns=rename_cols, inplace=True)
                
                # Handle insurance period if it exists
                if "insurance_period" in df.columns:
                    df[["insurance_period_start_date", "insurance_period_end_date"]] = df["insurance_period"].str.split(" - ", expand=True)
                    df["insurance_period_start_date"] = pd.to_datetime(df["insurance_period_start_date"], format="%d/%m/%Y")
                    df["insurance_period_end_date"] = pd.to_datetime(df["insurance_period_end_date"], format="%d/%m/%Y")
                    df.drop("insurance_period", axis=1, inplace=True)
                
                # Filter only columns that exist in the database schema
                valid_columns = [
                    "policy_number", "insured_name", "sum_insured", "premium",
                    "own_retention_ppn", "own_retention_sum_insured", "own_retention_premium",
                    "treaty_ppn", "treaty_sum_insured", "treaty_premium",
                    "facultative_outward_ppn", "facultative_outward_sum_insured", "facultative_outward_premium",
                    "insurance_period_start_date", "insurance_period_end_date"
                ]
                
                # Only keep columns that are in our target schema
                keep_cols = [col for col in df.columns if col in valid_columns]
                df_clean = df[keep_cols]
                
                # Make sure all columns are present (with NaNs for missing ones)
                for col in valid_columns:
                    if col not in df_clean:
                        df_clean[col] = None
                
                # Fill NA values with appropriate defaults
                df_clean = df_clean.fillna({
                    'insured_name': 'Unknown',
                    'sum_insured': 0.0,
                    'premium': 0.0,
                    'own_retention_ppn': 0.0,
                    'own_retention_sum_insured': 0.0,
                    'own_retention_premium': 0.0,
                    'treaty_ppn': 0.0,
                    'treaty_sum_insured': 0.0,
                    'treaty_premium': 0.0,
                    'facultative_outward_ppn': 0.0,
                    'facultative_outward_sum_insured': 0.0,
                    'facultative_outward_premium': 0.0
                })
                
                # Print final columns for debugging
                logger.info(f"Final columns to be inserted: {df_clean.columns.tolist()}")
                
                # Use direct psycopg2 connection for more control
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    dbname=DB_NAME,
                    user=DB_USERNAME,
                    password=DB_PASSWORD
                )
                
                try:
                    with conn.cursor() as cur:
                        # Filter rows with policy_number
                        df_valid = df_clean.dropna(subset=['policy_number'])
                        if len(df_valid) == 0:
                            logger.warning("No valid records found (all missing policy_number)")
                            return
                            
                        logger.info(f"Inserting {len(df_valid)} records")
                        
                        # Prepare data and column lists
                        columns = df_valid.columns.tolist()
                        values = [tuple(x) for x in df_valid.to_numpy()]
                        
                        # Create INSERT statement
                        insert_stmt = f"""
                        INSERT INTO insurance_policies 
                        ({', '.join(columns)})
                        VALUES %s
                        ON CONFLICT (policy_number) 
                        DO UPDATE SET {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'policy_number'])}
                        """
                        
                        # Execute batch insert
                        execute_values(cur, insert_stmt, values)
                        conn.commit()
                        logger.info(f"Successfully inserted {len(df_valid)} records")
                        
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to insert records: {e}")
                    raise
                finally:
                    conn.close()
            else:
                logger.warning("No sample Excel files found")
        
        # Final verification
        async with async_engine.begin() as conn:
            count_result = await conn.execute(text("SELECT COUNT(*) FROM insurance_policies"))
            final_count = count_result.scalar()
            logger.info(f"Final record count: {final_count}")
            
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_database())