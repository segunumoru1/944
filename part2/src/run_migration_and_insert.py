import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import Date, String, Float  # Import SQLAlchemy types
from config import settings

# SQL migration script split into individual statements
MIGRATION_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS insurance_policies (
        policy_number VARCHAR(255),
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
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_vector_id ON insurance_policies (vector_id);
    """
]

# Database connection details (from settings)
db_user = settings.DB_USERNAME
db_pass = settings.DB_PASSWORD
db_host = settings.DB_HOST
db_port = settings.DB_PORT
db_name = settings.DB_NAME

# Create SQLAlchemy engine
engine = create_engine(
    f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
)

# Step 1: Execute the migration statements
try:
    with engine.connect() as connection:
        # Use a transaction to ensure atomicity
        with connection.begin():  # Automatically commits or rolls back
            for statement in MIGRATION_STATEMENTS:
                connection.execute(text(statement.strip()))
        print("Migration script executed successfully!")
except Exception as e:
    print(f"Error executing migration script: {e}")
    raise

# Step 2: Load the processed data
try:
    df = pd.read_csv("processed_insurance.csv")
    print("Loaded data from processed_insurance.csv")
except Exception as e:
    print(f"Error loading CSV file: {e}")
    raise

# Step 3: Convert date columns to datetime64[ns]
try:
    df['insurance_period_start_date'] = pd.to_datetime(df['insurance_period_start_date'], errors='coerce')
    df['insurance_period_end_date'] = pd.to_datetime(df['insurance_period_end_date'], errors='coerce')
    print("Converted date columns to datetime64[ns]")
except Exception as e:
    print(f"Error converting date columns: {e}")
    raise

# Step 4: Insert data into the insurance_policies table
try:
    df.to_sql(
        "insurance_policies",
        engine,
        if_exists="append",
        index=False,
        dtype={
            'insurance_period_start_date': Date(),
            'insurance_period_end_date': Date(),
            'vector_id': String(length=36),
            'policy_number': String(length=255),
            'sum_insured': Float(precision=53),
            'premium': Float(precision=53),
            'own_retention_ppn': Float(precision=53),
            'own_retention_sum_insured': Float(precision=53),
            'own_retention_premium': Float(precision=53),
            'treaty_retention_ppn': Float(precision=53),
            'treaty_sum_insured': Float(precision=53),
            'treaty_premium': Float(precision=53)
        }
    )
    print("Data inserted successfully!")
except Exception as e:
    print(f"Error inserting data: {e}")
    raise

# Step 5: Verify column types in the database
try:
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'insurance_policies'
            AND column_name IN ('insurance_period_start_date', 'insurance_period_end_date', 'vector_id');
        """))
        for row in result:
            print(f"Column: {row.column_name}, Type: {row.data_type}")
except Exception as e:
    print(f"Error verifying column types: {e}")
    raise