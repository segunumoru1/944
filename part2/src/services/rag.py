from src.services.agent import query_agent
import logging

logger = logging.getLogger(__name__)

class InsuranceRAGSystem:
    def __init__(self):
        # No need for db_session as agent handles both SQL and vector search
        pass

    async def generate_response(self, query: str):
        """Generate response using the LangGraph agent"""
        try:
            # Use the agent for multi-step reasoning
            response = query_agent(query)
            return response
        except Exception as e:
            logger.error(f"RAG system error: {str(e)}")
            return "I apologize, but I'm having trouble generating a response at the moment."