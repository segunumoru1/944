import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage  
from src.config import settings

GEMINI_API_KEY = settings.GOOGLE_API_KEY

# Configure Gemini once at module level
if GEMINI_API_KEY:
    gemini_client = ChatGoogleGenerativeAI(
        google_api_key=GEMINI_API_KEY,
        model="gemini-1.5-pro",
        temperature=0.7,
        #max_output_tokens=2048
    )

async def query_gemini(prompt, model="gemini-1.5-pro"):  # Fix: Make async
    """Query Gemini with the latest Gemini 1.5 Pro model"""
    try:
        messages= [HumanMessage(content=prompt)]  # Fix: Use HumanMessage for Gemini
        response = await gemini_client.ainvoke(messages)
        return response.content
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {str(e)}")