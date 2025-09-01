import pandas as pd
import re
from datetime import datetime
import pandas as pd
from io import BytesIO


def preprocess_insurance_data(excel_path_or_content, output_csv: str = "processed_insurance.csv"):
    # Handle both file paths and bytes content
    if isinstance(excel_path_or_content, bytes):
        excel_file = BytesIO(excel_path_or_content)
    else:
        excel_file = excel_path_or_content
        
    # Read Excel sheets
    try:
        df1 = pd.read_excel(excel_file, sheet_name="data_1", header=7)
        df2 = pd.read_excel(excel_file, sheet_name="data_2", header=7)
        df3 = pd.read_excel(excel_file, sheet_name="data_3", header=7)
        
        # Combine dataframes
        df = pd.concat([df1, df2, df3], ignore_index=True)
        
        # Rename columns - ensure consistent naming
        rename_columns = {
            "INSURED": "insured_name",
            "POLICY NUMBER": "policy_number",
            "PERIOD OF INSURANCE": "insurance_period",
            "SUM INSURED": "sum_insured",
            "PREMIUM": "premium",
            "OWN RETENTION PPN": "own_retention_ppn",
            "OWN RETENTION SUM INSURED": "own_retention_sum_insured",
            "OWN RETENTION PREMIUM": "own_retention_premium",
            "TREATY PPN": "treaty_ppn",  # Changed from treaty_retention_ppn
            "TREATY SUM INSURED": "treaty_sum_insured",
            "TREATY PREMIUM": "treaty_premium",
            "FACULTATIVE OUTWARD PPN": "facultative_outward_ppn",
            "FACULTATIVE OUTWARD SUM INSURED": "facultative_outward_sum_insured",
            "FACULTATIVE OUTWARD PREMIUM": "facultative_outward_premium"
        }
        
        df.rename(columns=rename_columns, inplace=True)
        
        # Split insurance period into start and end dates
        df[['insurance_period_start_date', 'insurance_period_end_date']] = df['insurance_period'].str.split(' - ', expand=True)
        df['insurance_period_start_date'] = pd.to_datetime(df['insurance_period_start_date'])
        df['insurance_period_end_date'] = pd.to_datetime(df['insurance_period_end_date'])
        
        # Add missing facultative columns if they don't exist
        for col in ["facultative_outward_ppn", "facultative_outward_sum_insured", "facultative_outward_premium"]:
            if col not in df.columns:
                df[col] = 0.0
                
        # Ensure insured_name exists
        if "insured_name" not in df.columns:
            df["insured_name"] = "Unknown"
            
        # Save processed data
        df.to_csv(output_csv, index=False)
        return df
        
    except Exception as e:
        print(f"Error preprocessing data: {str(e)}")
        raise

def clean_policy_number(policy_number):
    """Clean policy numbers by removing special characters"""
    if pd.isna(policy_number):
        return ""
    
    # Remove non-printable characters and specific patterns
    cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F\u25A0]', '', str(policy_number))
    cleaned = re.sub(r'\s+[A-Z]/[A-Z]$', '', cleaned)
    return cleaned.strip()

def split_insurance_period(period_str):
    """Split insurance period into start and end dates"""
    if pd.isna(period_str):
        return None, None
    
    try:
        if ' - ' in str(period_str):
            start_str, end_str = str(period_str).split(' - ', 1)
            # Clean date strings
            start_str = re.sub(r'[^0-9/]', '', start_str)
            end_str = re.sub(r'[^0-9/]', '', end_str)
            
            # Parse dates
            start_date = datetime.strptime(start_str, '%d/%m/%Y') if start_str else None
            end_date = datetime.strptime(end_str, '%d/%m/%Y') if end_str else None
            
            return start_date, end_date
    except (ValueError, AttributeError):
        pass
    
    return None, None

def transform_excel_data(df):
    """Transform Excel data to match database schema"""
    # Clean policy numbers
    df['policy_number'] = df['policy_number'].apply(clean_policy_number)
    
    # Split insurance period
    df[['insurance_period_start_date', 'insurance_period_end_date']] = df['insurance_period'].apply(
        lambda x: pd.Series(split_insurance_period(x))
    )
    
    # Drop the original period column
    df.drop('insurance_period', axis=1, inplace=True)
    
    return df