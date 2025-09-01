# Insurance Policy RAG System

## Overview

This project implements a production-ready Agentic RAG (Retrieval Augmented Generation) FastAPI application for insurance policy data. The system allows users to ingest insurance policy data from Excel files, store it in a database, and perform intelligent searches and queries against the data.

## Part 1: System Design

See **Part 1** folder for the system architecture design and documentation.

## Part 2: Agentic RAG Implementation

### Features

- **Data Ingestion**: Upload Excel files containing insurance policy data
- **Data Processing**: Extract, transform, and validate insurance policy information
- **Vectorization**: Convert policy data into vector embeddings for semantic search
- **Query Interface**: Natural language query system for retrieving policy information
- **Authentication**: Secure API access with HTTP Basic Auth
- **Database Integration**: PostgreSQL storage with automatic schema migration
- **Vector Search**: Pinecone integration for efficient semantic search

### Technology Stack

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL
- **Vector Store**: Pinecone
- **Containerization**: Docker, Docker Compose
- **Authentication**: HTTP Basic Auth

### Data Schema

The system processes insurance policy data with the following schema:

| Field | Type | Description |
|-------|------|-------------|
| INSURED | String | Name of the insured party |
| POLICY NUMBER | String | Unique policy identifier |
| DEBIT NOTE | String | Debit note reference |
| PERIOD OF INSURANCE | String | Coverage period |
| SUM INSURED | Decimal | Total insured amount |
| PREMIUM | Decimal | Policy premium |
| OWN RETENTION PPN | String | Own retention percentage |
| OWN RETENTION SUM INSURED | Decimal | Own retention sum |
| OWN RETENTION PREMIUM | Decimal | Own retention premium |
| TREATY PPN | String | Treaty percentage |
| TREATY SUM INSURED | Decimal | Treaty sum insured |
| TREATY PREMIUM | Decimal | Treaty premium |
| FACULTATIVE OUTWARD PPN | String | Facultative outward percentage |
| FACULTATIVE OUTWARD SUM INSURED | Decimal | Facultative outward sum |
| FACULTATIVE OUTWARD PREMIUM | Decimal | Facultative outward premium |

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Git

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/insurance_db
POSTGRES_DB=insurance_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=insurance-policies

# Authentication
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secure_password

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Docker Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd insurance-policy-rag
```

2. Build and start the containers:
```bash
docker-compose up --build
```

3. Verify services are running:
```bash
docker-compose ps
```

4. Access the API at `http://localhost:8000`
5. Access the API documentation at `http://localhost:8000/docs`

### Local Development Setup

1. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/insurance_db"
export PINECONE_API_KEY="your_pinecone_api_key"
# ... other variables
```

4. Run the application:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

### Authentication

All endpoints are protected with HTTP Basic Authentication:

```bash
curl -u username:password http://localhost:8000/api/endpoint
```

### Endpoints

#### Health Check
**GET** `/health`

Returns the health status of the application and its dependencies.

```bash
curl -u admin:password http://localhost:8000/health
```

#### Data Ingestion
**POST** `/ingest`

Upload an Excel file with insurance policy data for processing and storage.

```bash
curl -X POST \
  -u admin:password \
  -F "file=@sample_data.xlsx" \
  http://localhost:8000/ingest
```

#### Query
**POST** `/query`

Perform semantic search and query insurance policy data using natural language.

```bash
curl -X POST \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"query": "Find all policies with premium above 10000"}' \
  http://localhost:8000/query
```

## Sample Data

A sample Excel file (`sample_insurance_data.xlsx`) is included in the repository for testing. This file contains realistic insurance policy data with the following columns:

- INSURED
- POLICY NUMBER
- DEBIT NOTE
- PERIOD OF INSURANCE
- SUM INSURED
- PREMIUM
- OWN RETENTION PPN
- OWN RETENTION SUM INSURED
- OWN RETENTION PREMIUM
- TREATY PPN
- TREATY SUM INSURED
- TREATY PREMIUM
- FACULTATIVE OUTWARD PPN
- FACULTATIVE OUTWARD SUM INSURED
- FACULTATIVE OUTWARD PREMIUM

## Error Handling

The system implements comprehensive error handling:

- **Input validation** for all API endpoints
- **Detailed error messages** for debugging
- **Graceful failure handling** for database and vector store operations
- **Structured logging** for monitoring and troubleshooting

## Limitations and Known Issues

- Large Excel files (>10MB) may experience timeout issues during processing
- Currently only supports specific Excel schema format
- Treaty field naming uses `treaty_retention_ppn` in database but may appear as `treaty_ppn` in some code paths

## Future Improvements

- Implement asynchronous processing for large file uploads
- Add support for batch operations
- Enhance vector search with hybrid retrieval techniques
- Implement more advanced data validation and cleaning
- Add unit and integration tests
- Implement rate limiting for API endpoints

## License

This project is proprietary and confidential.