import os
import uuid
import pandas as pd
import google.generativeai as genai
import pinecone
import logging
from typing import Dict, List, Any, Optional
import asyncio
from sqlalchemy import create_engine, text

from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# Constants
TABLE_NAME = "insurance_policies"
INDEX_NAME = "insurance-rag-index"
EMBEDDING_DIMENSION = 768  # Gemini embedding-001 dimension

class PineconeClient:
    def __init__(self):
        self.api_key = os.environ.get("PINECONE_API_KEY", settings.PINECONE_API_KEY)
        self.index_name = os.environ.get("PINECONE_INDEX", INDEX_NAME)
        self.google_api_key = os.environ.get("GOOGLE_API_KEY", settings.GOOGLE_API_KEY)
        self.index = None
        self.model = None
        
    async def init(self):
        """Initialize Pinecone and Google AI"""
        try:
            # Initialize Pinecone
            if not self.api_key:
                logger.error("PINECONE_API_KEY environment variable not set")
                raise ValueError("Pinecone API key not provided")
                
            pinecone.init(api_key=self.api_key)
            
            # Check if index exists, create if it doesn't
            if self.index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=EMBEDDING_DIMENSION,
                    metric="cosine"
                )
                
            # Connect to index
            self.index = pinecone.Index(self.index_name)
            
            # Initialize Google AI for embeddings
            if not self.google_api_key:
                logger.error("GOOGLE_API_KEY environment variable not set")
                raise ValueError("Google API key not provided")
                
            genai.configure(api_key=self.google_api_key)
            self.model = genai.GenerativeModel('embedding-001')
            
            logger.info("Pinecone client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Google AI"""
        try:
            result = self.model.embed_content(text)
            return result.embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def upsert_vector(self, vector_id: str, text: str, metadata: Dict[str, Any] = None) -> bool:
        """Upsert vector to Pinecone"""
        try:
            # Generate embedding
            embedding = await self.generate_embedding(text)
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
                
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)]
            )
            
            logger.info(f"Successfully upserted vector {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting vector: {str(e)}")
            return False
            
    async def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query Pinecone index"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query_text)
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            return results.matches
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            raise


def get_embedding(text):
    """Generate embedding for text using Google AI (synchronous version)"""
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        result = genai.embed_content(model='models/embedding-001', 
                                     content=text, 
                                     task_type="retrieval_document")
        return result['embedding']
    except Exception as e:
        logger.error(f"Gemini embedding API call failed: {e}")
        return None


def row_to_text(row):
    """Convert a database row to text for embedding"""
    return (
        f"Policy Number: {row.get('policy_number', '')}\n"
        f"Sum Insured: {row.get('sum_insured', '')}\n"
        f"Premium: {row.get('premium', '')}\n"
        f"Own Retention PPN: {row.get('own_retention_ppn', '')}\n"
        f"Own Retention Sum Insured: {row.get('own_retention_sum_insured', '')}\n"
        f"Own Retention Premium: {row.get('own_retention_premium', '')}\n"
        f"Treaty Retention PPN: {row.get('treaty_retention_ppn', '')}\n"
        f"Treaty Sum Insured: {row.get('treaty_sum_insured', '')}\n"
        f"Treaty Premium: {row.get('treaty_premium', '')}\n"
        f"Start Date: {row.get('insurance_period_start_date', '')}\n"
        f"End Date: {row.get('insurance_period_end_date', '')}"
    )


def index_database_records():
    """Index all records from the database to Pinecone"""
    try:
        # Step 1: Configure Google AI
        os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
        
        # Step 2: Connect to SQL DB and fetch data
        engine = create_engine(
            f"postgresql+psycopg2://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        query = f"SELECT * FROM {TABLE_NAME}"
        df = pd.read_sql(query, engine)
        logger.info(f"Retrieved {len(df)} records from database")
        
        if len(df) == 0:
            logger.warning("No records found in database, skipping indexing")
            return
        
        # Step 3: Generate unique vector IDs
        df['vector_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        # Step 4: Prepare text for embedding
        df['embedding_text'] = df.apply(row_to_text, axis=1)
        
        # Step 5: Generate embeddings using Gemini
        logger.info("Generating embeddings for database records...")
        df['embedding'] = df['embedding_text'].apply(get_embedding)
        
        # Remove rows where embedding failed
        df = df[df['embedding'].notnull()]
        logger.info(f"{len(df)} records successfully embedded")
        
        # Step 6: Initialize Pinecone
        logger.info("Initializing Pinecone...")
        pinecone.init(api_key=settings.PINECONE_API_KEY)
        
        # Create index if it doesn't exist
        if INDEX_NAME not in pinecone.list_indexes():
            logger.info(f"Creating Pinecone index: {INDEX_NAME}")
            pinecone.create_index(
                name=INDEX_NAME,
                dimension=EMBEDDING_DIMENSION,
                metric='cosine'
            )
        
        index = pinecone.Index(INDEX_NAME)
        
        # Step 7: Prepare data for upsert
        vectors = []
        for i, row in df.iterrows():
            vec_id = str(row['vector_id'])
            metadata = {
                'policy_number': str(row.get('policy_number', '')),
                'insured_name': str(row.get('insured_name', '')),
                'sum_insured': float(row.get('sum_insured', 0)),
                'premium': float(row.get('premium', 0)),
                'own_retention_ppn': float(row.get('own_retention_ppn', 0)),
                'own_retention_sum_insured': float(row.get('own_retention_sum_insured', 0)),
                'own_retention_premium': float(row.get('own_retention_premium', 0)),
                'treaty_retention_ppn': float(row.get('treaty_retention_ppn', 0)),
                'treaty_sum_insured': float(row.get('treaty_sum_insured', 0)),
                'treaty_premium': float(row.get('treaty_premium', 0)),
                'insurance_period_start_date': str(row.get('insurance_period_start_date', '')),
                'insurance_period_end_date': str(row.get('insurance_period_end_date', ''))
            }
            
            # Add facultative fields if they exist
            if 'facultative_outward_ppn' in row:
                metadata['facultative_outward_ppn'] = float(row.get('facultative_outward_ppn', 0))
            if 'facultative_outward_sum_insured' in row:
                metadata['facultative_outward_sum_insured'] = float(row.get('facultative_outward_sum_insured', 0))
            if 'facultative_outward_premium' in row:
                metadata['facultative_outward_premium'] = float(row.get('facultative_outward_premium', 0))
            
            vectors.append({
                'id': vec_id,
                'values': row['embedding'],
                'metadata': metadata
            })
        
        # Step 8: Upsert vectors to Pinecone
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            index.upsert(vectors=batch, namespace='insurance_namespace')
            logger.info(f"Upserted batch {i//batch_size + 1}/{(len(vectors)//batch_size) + 1} to Pinecone")
        
        logger.info(f"Successfully upserted {len(vectors)} vectors to Pinecone index '{INDEX_NAME}'.")
        
        # Step 9: Update PostgreSQL with vector_id
        with engine.begin() as conn:
            for _, row in df[['vector_id', 'policy_number']].iterrows():
                update_stmt = text(
                    "UPDATE insurance_policies SET vector_id = :vector_id WHERE policy_number = :policy_number"
                )
                conn.execute(update_stmt, {"vector_id": row['vector_id'], "policy_number": row['policy_number']})
        
        logger.info("Updated database with vector IDs.")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing database records: {e}")
        raise


def query_rag(user_query, top_k=5):
    """Query the RAG system with natural language"""
    try:
        # Initialize Pinecone
        pinecone.init(api_key=settings.PINECONE_API_KEY)
        index = pinecone.Index(INDEX_NAME)
        
        # Generate embedding for query
        query_emb = get_embedding(user_query)
        if not query_emb:
            logger.error("Failed to generate embedding for query")
            return None
            
        # Query Pinecone
        results = index.query(
            vector=query_emb, 
            top_k=top_k, 
            include_metadata=True,
            namespace='insurance_namespace'
        )
        
        return results
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return None


# Run indexing if script is executed directly
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--index":
        logger.info("Starting database indexing process...")
        index_database_records()
        logger.info("Indexing completed")
    else:
        logger.info("Use --index flag to run database indexing")