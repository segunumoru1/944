from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.ingestion import ingest_excel_data
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/excel")
async def ingest_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests Excel file containing insurance data
    
    - **file**: Excel file with insurance data sheets
    - Returns: Ingestion summary with record count
    """
    try:
        logger.info(f"Received file: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Process the Excel file
        result = await ingest_excel_data(db, file_content, file.filename)
        
        # Add explicit commit check
        try:
            # This is to verify if the commit happened
            count_query = "SELECT COUNT(*) FROM insurance_policies"
            count_result = await db.execute(count_query)
            actual_count = count_result.scalar()
            logger.info(f"Verified record count after ingestion: {actual_count}")
            
            if actual_count == 0:
                logger.error("Data appears to be committed but no records found")
                raise HTTPException(status_code=500, detail="Data ingestion failed - no records created")
                
        except Exception as e:
            logger.error(f"Verification query failed: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")