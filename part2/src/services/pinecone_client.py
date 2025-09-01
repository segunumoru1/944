import os
import pandas as pd
from sqlalchemy import create_engine
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import uuid
import logging
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

TABLE_NAME = "insurance_policies"
INDEX_NAME = "insurance-rag-index"
EMBEDDING_DIMENSION = 768  # Gemini embedding-001 dimension (adjust if using different model)

# Configure Gemini
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
model = 'models/embedding-001'  # Use Gemini embedding model

# Step 2: Connect to SQL DB and fetch data
try:
    engine = create_engine(
        f"postgresql+psycopg2://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    query = f"SELECT * FROM {TABLE_NAME}"
    df = pd.read_sql(query, engine)
except Exception as e:
    logging.error(f"Database connection or query failed: {e}")
    raise

# Step 3: Generate unique vector IDs
df['vector_id'] = [str(uuid.uuid4()) for _ in range(len(df))]

# Step 4: Prepare text for embedding
def row_to_text(row):
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

df['embedding_text'] = df.apply(row_to_text, axis=1)

# Step 5: Generate embeddings using Gemini
def get_embedding(text):
    try:
        result = genai.embed_content(model=model, content=text, task_type="retrieval_document")
        return result['embedding']
    except Exception as e:
        logging.error(f"Gemini embedding API call failed: {e}")
        return None

df['embedding'] = df['embedding_text'].apply(get_embedding)

# Remove rows where embedding failed
df = df[df['embedding'].notnull()]

# Step 6: Initialize Pinecone
try:
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    # Create index if it doesn't exist
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
    index = pc.Index(INDEX_NAME)
except Exception as e:
    logging.error(f"Pinecone initialization or index creation failed: {e}")
    raise

# Step 7: Prepare data for upsert
vectors = []
for i, row in df.iterrows():
    vec_id = str(row['vector_id'])
    metadata = {
        'policy_number': row.get('policy_number', ''),
        'insured_name': row.get('insured_name', ''),
        'sum_insured': row.get('sum_insured', ''),
        'premium': row.get('premium', ''),
        'own_retention_ppn': row.get('own_retention_ppn', ''),
        'own_retention_sum_insured': row.get('own_retention_sum_insured', ''),
        'own_retention_premium': row.get('own_retention_premium', ''),
        'treaty_ppn': row.get('treaty_ppn', ''),  # Changed from treaty_retention_ppn
        'treaty_sum_insured': row.get('treaty_sum_insured', ''),
        'treaty_premium': row.get('treaty_premium', ''),
        'facultative_outward_ppn': row.get('facultative_outward_ppn', ''),
        'facultative_outward_sum_insured': row.get('facultative_outward_sum_insured', ''),
        'facultative_outward_premium': row.get('facultative_outward_premium', ''),
        'insurance_period_start_date': str(row.get('insurance_period_start_date', '')),
        'insurance_period_end_date': str(row.get('insurance_period_end_date', ''))
    }
    vectors.append({
        'id': vec_id,
        'values': row['embedding'],
        'metadata': metadata
    })

# Step 8: Upsert vectors to Pinecone
try:
    index.upsert(vectors=vectors, namespace='insurance_namespace')
    logging.info(f"Successfully upserted {len(vectors)} vectors to Pinecone index '{INDEX_NAME}'.")
except Exception as e:
    logging.error(f"Pinecone upsert failed: {e}")
    raise

# Step 9: Update PostgreSQL with vector_id
from sqlalchemy import text

try:
    with engine.begin() as conn:
        for _, row in df[['vector_id', 'policy_number']].iterrows():
            update_stmt = text(
                "UPDATE insurance_policies SET vector_id = :vector_id WHERE policy_number = :policy_number"
            )
            conn.execute(update_stmt, {"vector_id": row['vector_id'], "policy_number": row['policy_number']})
    logging.info("Updated database with vector IDs.")
except Exception as e:
    logging.error(f"Failed to update database with vector IDs: {e}")

# For RAG usage example (not part of setup, but for completeness):
def query_rag(user_query):
    try:
        query_emb = get_embedding(user_query)
        results = index.query(vector=query_emb, top_k=5, include_metadata=True)
        return results
    except Exception as e:
        logging.error(f"RAG query failed: {e}")
        return None