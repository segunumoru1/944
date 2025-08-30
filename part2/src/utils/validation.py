import pandas as pd
import re
from datetime import datetime
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def validate_excel_file(file_content: bytes, filename: str):
    """Validate Excel file structure and content"""
    # Check file extension
    if not filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Only Excel files (.xlsx, .xls) are supported")
    
    try:
        # Try to read the Excel file
        excel_data = pd.ExcelFile(file_content)
        
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

def validate_insurance_data(df: pd.DataFrame):
    """Validate insurance data against required schema"""
    required_columns = {
        "policy_number": "string",
        "sum_insured": "float",
        "premium": "float",
        "own_retention_ppn": "float",
        "own_retention_sum_insured": "float",
        "own_retention_premium": "float",
        "treaty_ppn": "float",
        "treaty_sum_insured": "float",
        "treaty_premium": "float",
        "insurance_period": "string"
    }
    
    # Check for required columns
    missing_columns = [col for col in required_columns.keys() if col not in df.columns]
    if missing_columns:
        raise HTTPException(400, f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate data types
    for column, expected_type in required_columns.items():
        if column in df.columns:
            if expected_type == "float" and not pd.api.types.is_numeric_dtype(df[column]):
                raise HTTPException(400, f"Column {column} must contain numeric values")
    
    return True

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