from fastapi import APIRouter, HTTPException, Depends
from src.services.rag import InsuranceRAGSystem
from src.schemas import QueryRequest, QueryResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("", response_model=QueryResponse)
async def query_insurance_data(request: QueryRequest):
    """
    Query insurance data using natural language with multi-step reasoning
    
    - **question**: Natural language question about insurance data
    - Returns: Answer with source citations
    """
    try:
        rag_system = InsuranceRAGSystem()
        response = await rag_system.generate_response(request.question)
        
        return QueryResponse(
            answer=response,
            sources=["Database query results", "Semantic search results"]
        )
    
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(500, f"Failed to process query: {str(e)}")