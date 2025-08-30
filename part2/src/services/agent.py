from langgraph.prebuilt import create_react_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.tools import Tool
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from sqlalchemy import create_engine
from src.config import settings
from src.llm import llm
import logging
from typing import List

logger = logging.getLogger(__name__)

# Create synchronous engine for LangChain
sync_engine = create_engine(
    f"postgresql+psycopg2://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# SQL Tool
db = SQLDatabase(engine=sync_engine)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True
)

def sql_query_tool(query: str) -> str:
    """Execute SQL queries on insurance database"""
    try:
        result = sql_agent.run(query)
        return str(result)
    except Exception as e:
        logger.error(f"SQL query error: {str(e)}")
        return f"Error executing SQL query: {str(e)}"

# RAG Tool
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
)

vectorstore = PineconeVectorStore(
    index_name=settings.PINECONE_INDEX_NAME,
    embedding=embeddings,
    namespace="insurance_namespace"
)

def rag_search_tool(query: str) -> str:
    """Search for similar insurance policies using semantic search"""
    try:
        docs = vectorstore.similarity_search(query, k=5)
        return "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        return f"Error retrieving documents: {str(e)}"

# Create tools
tools = [
    Tool(
        name="sql_query",
        func=sql_query_tool,
        description="Use for structured queries on insurance data like sums, averages, filters, and specific policy details."
    ),
    Tool(
        name="rag_search",
        func=rag_search_tool,
        description="Use for semantic search on policy details, finding similar policies, or understanding policy context."
    )
]

# Create LangGraph ReAct Agent
agent = create_react_agent(llm, tools)

def query_agent(question: str) -> str:
    """Query the agent with a question and return the response"""
    try:
        response = agent.invoke({"messages": [{"role": "user", "content": question}]})
        return response['messages'][-1].content
    except Exception as e:
        logger.error(f"Agent query error: {str(e)}")
        return "I apologize, but I encountered an error while processing your query."