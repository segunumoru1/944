import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage  
from src.config import settings

GEMINI_API_KEY = settings.GOOGLE_API_KEY

# Configure Gemini for LangChain
llm = ChatGoogleGenerativeAI(
    google_api_key=GEMINI_API_KEY,
    model="gemini-1.5-pro",
    temperature=0.7
)

async def query_gemini(prompt, model="gemini-1.5-pro"):
    """Query Gemini with the latest Gemini 1.5 Pro model"""
    try:
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {str(e)}")