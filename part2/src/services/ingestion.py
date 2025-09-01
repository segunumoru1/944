import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.data_processing import transform_excel_data
from src.utils.validation import validate_excel_file, validate_insurance_data
from fastapi import HTTPException
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

async def ingest_excel_data(session: AsyncSession, file_content: bytes, filename: str):
    """Process and ingest Excel data into database"""
    try:
        # Validate Excel file
        validate_excel_file(file_content, filename)
        
        # Use BytesIO to handle file content
        file_io = BytesIO(file_content)
        
        # Read Excel sheets - header at row 7 (0-indexed)
        dfs = {}
        excel_file = pd.ExcelFile(file_io)
        for sheet in excel_file.sheet_names:
            dfs[sheet] = pd.read_excel(excel_file, sheet_name=sheet, header=0)
        
        # Combine all sheets
        df_combined = pd.concat(dfs.values(), ignore_index=True)
        
        # Column mapping - Excel column names to database column names
        column_mapping = {
            "INSURED": "insured_name",
            "POLICY NUMBER": "policy_number",
            "PERIOD OF INSURANCE": "insurance_period",
            "SUM INSURED": "sum_insured",
            "PREMIUM": "premium",
            "OWN RETENTION PPN": "own_retention_ppn",
            "OWN RETENTION SUM INSURED": "own_retention_sum_insured", 
            "OWN RETENTION PREMIUM": "own_retention_premium",
            "TREATY PPN": "treaty_retention_ppn",
            "TREATY SUM INSURED": "treaty_sum_insured",
            "TREATY PREMIUM": "treaty_premium",
            "FACULTATIVE OUTWARD PPN": "facultative_outward_ppn",
            "FACULTATIVE OUTWARD SUM INSURED": "facultative_outward_sum_insured",
            "FACULTATIVE OUTWARD PREMIUM": "facultative_outward_premium"
        }
        
        # Rename columns based on mapping
        df_combined.rename(columns=column_mapping, inplace=True)
        
        # Process insurance period field
        if "insurance_period" in df_combined.columns:
            # Split period into start and end dates
            df_combined[['insurance_period_start_date', 'insurance_period_end_date']] = df_combined['insurance_period'].str.split(' - ', expand=True)
            
            # Convert to datetime
            df_combined['insurance_period_start_date'] = pd.to_datetime(df_combined['insurance_period_start_date'], format='%d/%m/%Y')
            df_combined['insurance_period_end_date'] = pd.to_datetime(df_combined['insurance_period_end_date'], format='%d/%m/%Y')
            
            # Drop original period column
            df_combined.drop('insurance_period', axis=1, inplace=True)
        
        # Check if required columns exist in table before inserting
        # First, check database table structure
        table_structure_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'insurance_policies'")
        result = await session.execute(table_structure_query)
        existing_columns = [row[0] for row in result.all()]
        
        logger.info(f"Existing columns in database: {existing_columns}")
        
        # Build insert statement dynamically based on existing columns
        columns_to_insert = []
        placeholders = []
        update_statements = []
        params = {}
        
        # Add columns that exist in both dataframe and database
        for idx, row in df_combined.iterrows():
            row_params = {}
            for col in df_combined.columns:
                if col in existing_columns:
                    if idx == 0:  # Only add column name and placeholder once
                        columns_to_insert.append(col)
                        placeholders.append(f":{col}")
                        update_statements.append(f"{col} = EXCLUDED.{col}")
                    row_params[col] = row.get(col)
            
            # Construct and execute insert statement
            if columns_to_insert:
                insert_stmt = text(f"""
                    INSERT INTO insurance_policies 
                    ({', '.join(columns_to_insert)})
                    VALUES 
                    ({', '.join(placeholders)})
                    ON CONFLICT (policy_number) DO UPDATE SET
                    {', '.join(update_statements)}
                """)
                
                await session.execute(insert_stmt, row_params)
        
        await session.commit()
        return {"message": "Data ingested successfully", "records_processed": len(df_combined)}
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error ingesting data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting data: {str(e)}")