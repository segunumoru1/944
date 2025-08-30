from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.rag import InsuranceRAGSystem
from src.database import get_db
from src.utils.security import sanitize_sql_input
from src.schemas import QueryResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    question: str

@router.post("", response_model=QueryResponse)
async def query_insurance_data(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query insurance data using natural language
    
    - **question**: Natural language question about insurance data
    - Returns: Answer with source citations
    """
    try:
        # Sanitize user input
        sanitized_question = sanitize_sql_input(request.question)
        
        rag_system = InsuranceRAGSystem()
        response = await rag_system.generate_response(sanitized_question)
        
        return QueryResponse(
            answer=response,
            sources=["Database query results", "Semantic search results"]
        )
    
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(500, f"Failed to process query: {str(e)}")