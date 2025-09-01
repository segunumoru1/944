import pandas as pd
import re
from datetime import datetime
from fastapi import HTTPException
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

def validate_excel_file(file_content: bytes, filename: str):
    """Validate that the uploaded file is a valid Excel file"""
    if not filename.endswith(('.xls', '.xlsx')):
        raise ValueError("File must be an Excel file (.xls or .xlsx)")
    
    # Use BytesIO to handle bytes content properly
    try:
        excel_data = pd.ExcelFile(BytesIO(file_content))
        
        # Check if required sheets exist
        required_sheets = ['data_1', 'data_2', 'data_3']
        available_sheets = excel_data.sheet_names
        
        missing_sheets = [sheet for sheet in required_sheets if sheet not in available_sheets]
        if missing_sheets:
            raise HTTPException(400, f"Missing required sheets: {', '.join(missing_sheets)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Excel validation error: {str(e)}")
        raise HTTPException(400, f"Invalid Excel file: {str(e)}")

def validate_insurance_data(df_or_file):
    """Validate insurance data against required schema"""
    
    # If input is file content, convert to DataFrame
    if not isinstance(df_or_file, pd.DataFrame):
        if isinstance(df_or_file, bytes):
            excel_data = pd.ExcelFile(BytesIO(df_or_file))
        else:
            excel_data = pd.ExcelFile(df_or_file)
        
        sheet_names = excel_data.sheet_names
        df_list = []
        
        for sheet in sheet_names:
            df_sheet = pd.read_excel(excel_data, sheet_name=sheet, header=7)
            df_list.append(df_sheet)
            
        df = pd.concat(df_list, ignore_index=True)
    else:
        df = df_or_file
    
    # Define required columns with data types
    required_columns = {
        "policy_number": "string",
        "sum_insured": "float",
        "premium": "float",
        "own_retention_ppn": "float",
        "own_retention_sum_insured": "float",
        "own_retention_premium": "float",
        "treaty_retention_ppn": "float",  # Match what's in the CSV for now
        "treaty_sum_insured": "float",
        "treaty_premium": "float"
    }
    
    # Check for missing required columns
    missing_columns = []
    for col in required_columns:
        if col not in df.columns:
            if col == "treaty_retention_ppn" and "treaty_ppn" in df.columns:
                # Rename to match expected schema
                df["treaty_retention_ppn"] = df["treaty_ppn"]
            else:
                missing_columns.append(col)
    
    # Add missing columns with default values
    if "insured_name" not in df.columns:
        df["insured_name"] = "Unknown"
    
    for col in ["facultative_outward_ppn", "facultative_outward_sum_insured", 
                "facultative_outward_premium"]:
        if col not in df.columns:
            df[col] = 0.0
    
    # Handle insurance period dates
    if "insurance_period" in df.columns:
        df[['insurance_period_start_date', 'insurance_period_end_date']] = df['insurance_period'].str.split(' - ', expand=True)
        df['insurance_period_start_date'] = pd.to_datetime(df['insurance_period_start_date'])
        df['insurance_period_end_date'] = pd.to_datetime(df['insurance_period_end_date'])
    
    # Final check for any remaining missing columns
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    return df

def sanitize_input(input_string: str):
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[;\\\'"<>%$]', '', str(input_string))
    # Limit length
    sanitized = sanitized[:1000]
    
    return sanitized

def validate_date_format(date_string: str):
    """Validate date format (DD/MM/YYYY)"""
    try:
        datetime.strptime(date_string, '%d/%m/%Y')
        return True
    except ValueError:
        return False