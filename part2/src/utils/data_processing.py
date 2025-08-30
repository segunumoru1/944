import pandas as pd
import re
from datetime import datetime

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

