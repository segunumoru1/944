import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.data_processing import transform_excel_data
from src.utils.validation import validate_excel_file, validate_insurance_data
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def ingest_excel_data(session: AsyncSession, file_content: bytes, filename: str):
    """Process and ingest Excel data into database"""
    try:
        # Validate Excel file
        validate_excel_file(file_content, filename)
        
        # Read Excel file
        df = pd.read_excel(file_content, sheet_name=None)
        
        # Process each sheet
        all_data = []
        for sheet_name, sheet_data in df.items():
            if sheet_name.startswith('data_'):
                # Validate data structure
                validate_insurance_data(sheet_data)
                
                # Clean and transform data
                transformed = transform_excel_data(sheet_data)
                all_data.append(transformed)
        
        # Combine all sheets
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Insert into database
        for _, row in combined_df.iterrows():
            insert_stmt = text("""
                INSERT INTO insurance_policies 
                (policy_number, sum_insured, premium, own_retention_ppn, 
                 own_retention_sum_insured, own_retention_premium, treaty_ppn,
                 treaty_sum_insured, treaty_premium, insurance_period_start_date, 
                 insurance_period_end_date)
                VALUES 
                (:policy_number, :sum_insured, :premium, :own_retention_ppn,
                 :own_retention_sum_insured, :own_retention_premium, :treaty_ppn,
                 :treaty_sum_insured, :treaty_premium, :insurance_period_start_date,
                 :insurance_period_end_date)
                ON CONFLICT (policy_number) DO UPDATE SET
                sum_insured = EXCLUDED.sum_insured,
                premium = EXCLUDED.premium,
                own_retention_ppn = EXCLUDED.own_retention_ppn,
                own_retention_sum_insured = EXCLUDED.own_retention_sum_insured,
                own_retention_premium = EXCLUDED.own_retention_premium,
                treaty_ppn = EXCLUDED.treaty_ppn,
                treaty_sum_insured = EXCLUDED.treaty_sum_insured,
                treaty_premium = EXCLUDED.treaty_premium,
                insurance_period_start_date = EXCLUDED.insurance_period_start_date,
                insurance_period_end_date = EXCLUDED.insurance_period_end_date
            """)
            
            await session.execute(insert_stmt, {
                "policy_number": row.get("policy_number"),
                "sum_insured": row.get("sum_insured"),
                "premium": row.get("premium"),
                "own_retention_ppn": row.get("own_retention_ppn"),
                "own_retention_sum_insured": row.get("own_retention_sum_insured"),
                "own_retention_premium": row.get("own_retention_premium"),
                "treaty_ppn": row.get("treaty_ppn"),
                "treaty_sum_insured": row.get("treaty_sum_insured"),
                "treaty_premium": row.get("treaty_premium"),
                "insurance_period_start_date": row.get("insurance_period_start_date"),
                "insurance_period_end_date": row.get("insurance_period_end_date")
            })
        
        await session.commit()
        return {"message": "Data ingested successfully", "records_processed": len(combined_df)}
    
    except Exception as e:
        await session.rollback()
        logger.error(f"Error ingesting data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error ingesting data")