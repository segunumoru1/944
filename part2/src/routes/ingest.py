from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.ingestion import ingest_excel_data
from src.database import get_db
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
        # Validate file type
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "Only Excel files are supported")
        
        # Read file content
        content = await file.read()
        
        # Process and ingest data
        result = await ingest_excel_data(db, content, file.filename)
        
        return {
            "status": "success",
            "message": result["message"],
            "records_processed": result["records_processed"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel ingestion error: {str(e)}")
        raise HTTPException(500, f"Failed to process Excel file: {str(e)}")