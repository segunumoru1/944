import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
import logging
from io import BytesIO
from ..services.pinecone_client import PineconeClient
import uuid

logger = logging.getLogger(__name__)

async def ingest_excel_data(session: AsyncSession, file_content: bytes, filename: str):
    """Process and ingest Excel data into database and vector store"""
    try:
        # Use BytesIO to handle file content
        file_io = BytesIO(file_content)
        
        # Load Excel file (all sheets)
        excel_file = pd.ExcelFile(file_io)
        all_dfs = []
        
        # Process each sheet
        for sheet_name in excel_file.sheet_names:
            # First row is often a header, so we'll use header=0
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
            all_dfs.append(df)
        
        # Combine all dataframes
        df_combined = pd.concat(all_dfs, ignore_index=True)
        
        # Rename columns - map Excel column names to database column names
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
        
        # Only rename columns that exist
        cols_to_rename = {k: v for k, v in column_mapping.items() if k in df_combined.columns}
        df_combined.rename(columns=cols_to_rename, inplace=True)
        
        # Process insurance period into start and end dates
        if "insurance_period" in df_combined.columns:
            df_combined[['insurance_period_start_date', 'insurance_period_end_date']] = df_combined['insurance_period'].str.split(' - ', expand=True)
            df_combined['insurance_period_start_date'] = pd.to_datetime(df_combined['insurance_period_start_date'], format='%d/%m/%Y')
            df_combined['insurance_period_end_date'] = pd.to_datetime(df_combined['insurance_period_end_date'], format='%d/%m/%Y')
            
        # Generate vector IDs for new records
        df_combined['vector_id'] = [str(uuid.uuid4()) for _ in range(len(df_combined))]
        
        # Initialize Pinecone client
        pinecone_client = PineconeClient()
        await pinecone_client.init()
        
        # Log the data we're about to insert
        logger.info(f"Preparing to insert {len(df_combined)} records")
        
        # Keep track of successful inserts
        successful_inserts = 0
        
        # Process each row
        for _, row in df_combined.iterrows():
            try:
                # Ensure policy_number is not null
                policy_number = row.get('policy_number', '')
                if not policy_number:
                    logger.warning("Skipping row with empty policy_number")
                    continue
                    
                # Debug: Log the row we're about to insert
                logger.info(f"Inserting policy: {policy_number}")
                
                # Prepare values for database insertion
                values = {col: row.get(col) for col in [
                    'policy_number', 'insured_name', 'sum_insured', 'premium',
                    'own_retention_ppn', 'own_retention_sum_insured', 'own_retention_premium',
                    'treaty_retention_ppn', 'treaty_sum_insured', 'treaty_premium',
                    'facultative_outward_ppn', 'facultative_outward_sum_insured', 
                    'facultative_outward_premium', 'insurance_period_start_date',
                    'insurance_period_end_date', 'vector_id'
                ] if col in row}
                
                # Insert into database using parameterized query
                columns = ', '.join(values.keys())
                placeholders = ', '.join([f":{col}" for col in values.keys()])
                update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in values.keys() if col != 'policy_number'])
                
                query = f"""
                INSERT INTO insurance_policies ({columns})
                VALUES ({placeholders})
                ON CONFLICT (policy_number) DO UPDATE SET {update_clause}
                """
                
                await session.execute(text(query), values)
                
                # Generate embedding and store in Pinecone
                policy_text = f"Policy {policy_number} for {row.get('insured_name', 'Unknown')} with sum insured {row.get('sum_insured', 0)} and premium {row.get('premium', 0)}"
                
                # Store in Pinecone
                await pinecone_client.upsert_vector(
                    row['vector_id'],
                    policy_text,
                    {
                        'policy_number': str(row.get('policy_number', '')),
                        'insured_name': str(row.get('insured_name', '')),
                        'sum_insured': float(row.get('sum_insured', 0)),
                        'premium': float(row.get('premium', 0))
                    }
                )
                
                successful_inserts += 1
                
            except Exception as e:
                logger.error(f"Error processing row {_}: {str(e)}")
                # Continue with next row instead of failing entirely
        
        # Commit the transaction if any records were processed
        if successful_inserts > 0:
            await session.commit()
            logger.info(f"Successfully inserted {successful_inserts} records")
            return {"status": "success", "message": "Data ingested successfully", "records_processed": successful_inserts}
        else:
            await session.rollback()
            logger.error("No records were successfully processed")
            raise HTTPException(status_code=500, detail="No records were successfully processed")
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error during data ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting data: {str(e)}")