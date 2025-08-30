# data_preprocessing_pipeline.py
# The script includes reading Excel data, cleaning, transformation, handling missing values, and inserting into a PostgreSQL database.

import pandas as pd
from sqlalchemy import create_engine

# Step 1: Read the Excel files (assuming the file path is '../sample_data.xlsx')
def read_data(file_path='../sample_data.xlsx'):
    df1 = pd.read_excel(file_path, sheet_name="data_1", header=7)
    df2 = pd.read_excel(file_path, sheet_name="data_2", header=7)
    df3 = pd.read_excel(file_path, sheet_name="data_3", header=7)
    return df1, df2, df3

# Step 2: Clean the data (drop unnecessary columns)
def clean_data(df):
    return df.drop(columns=["INSURED", "SN", "DEBIT NOTE"], axis=1, errors='ignore')

# Step 3: Concatenate the dataframes
def concatenate_dataframes(df1, df2, df3):
    return pd.concat([df1, df2, df3], ignore_index=True)

# Step 4: Rename columns to meaningful names
def rename_columns(df):
    rename_map = {
        'POLICY NUMBER': 'policy_number',
        'PERIOD OF INSURANCE': 'insurance_period',
        'SUM INSURED': 'sum_insured',
        'PREMIUM': 'premium',
        'PPN': 'own_retention_ppn',
        'SUM INSURED.1': 'own_retention_sum_insured',
        'PREMIUM.1': 'own_retention_premium',
        'PPN.1': 'treaty_retention_ppn',
        'SUM INSURED.2': 'treaty_sum_insured',
        'PREMIUM.2': 'treaty_premium',
        'PPN.2': 'facultative_outward_ppn',
        'SUM INSURED.3': 'facultative_outward_sum_insured',
        'PREMIUM.3': 'facultative_outward_premium'
    }
    return df.rename(columns=rename_map)

# Step 5: Transform data (split insurance period, select columns, convert types)
def transform_data(df):
    # Split insurance_period into start and end dates
    df[['insurance_period_start_date', 'insurance_period_end_date']] = df['insurance_period'].str.split(' - ', expand=True)
    
    # Desired columns and types (based on notebook, excluding 'insured_name' as it's dropped)
    desired_columns = {
        "policy_number": "string",
        "sum_insured": "float",
        "premium": "float",
        "own_retention_ppn": "float",
        "own_retention_sum_insured": "float",
        "own_retention_premium": "float",
        "treaty_retention_ppn": "float",  # Included as per initial rename
        "treaty_sum_insured": "float",
        "treaty_premium": "float",
        "insurance_period_start_date": "datetime64[ns]",
        "insurance_period_end_date": "datetime64[ns]",
    }
    
    # Select only desired columns that exist
    df = df[[col for col in desired_columns.keys() if col in df.columns]]
    
    # Convert data types
    for col, dtype in desired_columns.items():
        if col in df.columns:
            if dtype == "string":
                df[col] = df[col].astype("string")
            elif dtype == "float":
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == "datetime64[ns]":
                df[col] = pd.to_datetime(df[col], errors="coerce")
    
    return df

# Step 6: Handle missing values (fill dates with mode)
def handle_missing_values(df):
    if 'insurance_period_start_date' in df.columns:
        mode_start = df["insurance_period_start_date"].mode()
        if not mode_start.empty:
            df["insurance_period_start_date"].fillna(mode_start.iloc[0], inplace=True)
    
    if 'insurance_period_end_date' in df.columns:
        mode_end = df["insurance_period_end_date"].mode()
        if not mode_end.empty:
            df["insurance_period_end_date"].fillna(mode_end.iloc[0], inplace=True)
    
    # Handle other potential NaNs (e.g., fill floats with 0 or drop, based on notebook - here we assume fill 0 for numerics)
    numeric_cols = df.select_dtypes(include=['float']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

# Step 7: Insert data into SQL database
def insert_to_db(df, db_user, db_pass, db_host, db_port, db_name, table_name="insurance_policies"):
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print("Data inserted successfully!")

# Main pipeline function
def run_pipeline(excel_file_path='../sample_data.xlsx', db_user="postgres", db_pass="your_password", db_host="localhost", db_port="5432", db_name="insurance_db"):
    df1, df2, df3 = read_data(excel_file_path)
    df1 = clean_data(df1)
    df2 = clean_data(df2)
    df3 = clean_data(df3)
    merged_df = concatenate_dataframes(df1, df2, df3)
    merged_df = rename_columns(merged_df)
    merged_df = transform_data(merged_df)
    merged_df = handle_missing_values(merged_df)
    # Optional: Save to CSV
    merged_df.to_csv('processed_insurance.csv', index=False)
    insert_to_db(merged_df, db_user, db_pass, db_host, db_port, db_name)

# Run the pipeline (update DB credentials)
if __name__ == "__main__":
    run_pipeline(
        excel_file_path='../sample_data.xlsx',
        db_user="postgres",
        db_pass="XlxKtnW8NRVSIEHC3CzKihPQRATGIsqo0525SORi265JeZdSs1RakwwzZAyM3W9E",
        db_host="138.197.129.114",
        db_port="5476",
        db_name="insurance_db"
    )