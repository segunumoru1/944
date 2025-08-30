# DESIGN\_ANALYSIS.md

RAG Ingestion System – Design Analysis (Excel → Postgres + Pinecone)

---

## Client Application (Web/Mobile)

* **Design Decision:** Chosen as the entry point to let users directly upload Excel files, ensuring accessibility. 
*Why:* Provides familiar interface and reduces onboarding friction.
* **Challenges/Mitigations:** Must handle file size limits and upload failures → use chunked uploads and client-side validation.
* **Trade-offs:** Rich UX requires more development effort vs. simple CLI ingestion.
* **Alternatives Considered:** CLI batch ingestion for ops teams; scheduled ETL jobs for automation.

---

## API Gateway (FastAPI)

* **Design Decision:** FastAPI chosen for lightweight, async API handling of `/ingest-excel`. 
*Why:* High developer productivity with async support and type validation.
* **Challenges/Mitigations:** Default single-threaded model → mitigate with Uvicorn/Gunicorn + worker scaling.
* **Trade-offs:** Faster iteration vs. lower built-in enterprise features compared to heavier frameworks.
* **Alternatives Considered:** Flask + Celery for async, Django REST Framework, Spring Boot for JVM shops.

---

## Excel Parser & Validator

* **Design Decision:** Dedicated parsing layer enforces schema compliance. 
*Why:* Guarantees data integrity before entering pipeline.
* **Challenges/Mitigations:** Memory spikes on large files → mitigate via streaming reads and schema-first validation.
* **Trade-offs:** Stricter validation reduces ingestion speed but avoids downstream errors.
* **Alternatives Considered:** Apache POI (Java), Pandas pipelines, external ETL services.

---

## Data Transformer

* **Design Decision:** Transformation isolates logic for splitting periods and normalizing fields. *Why:* Keeps ingestion modular and schema-aligned.
* **Challenges/Mitigations:** Complex transformation logic grows with evolving business rules → mitigate via config-driven mappings.
* **Trade-offs:** Flexibility of Python scripts vs. performance overhead on very large datasets.
* **Alternatives Considered:** Spark ETL for scale, dbt for SQL-centric pipelines.

---

## PostgreSQL Database

* **Design Decision:** Postgres as primary structured store for policies. 
*Why:* ACID compliance, strong schema, mature ecosystem.
* **Challenges/Mitigations:** Scaling bottlenecks under heavy concurrency → mitigate with connection pooling + partitioning.
* **Trade-offs:** Relational guarantees vs. less flexibility compared to NoSQL.
* **Alternatives Considered:** Aurora (managed scaling), MySQL, MongoDB for schema-loose data.

---

## Embedding Generator (Gemini)

* **Design Decision:** External embedding service chosen. 
*Why:* High-quality embeddings critical for semantic retrieval.
* **Challenges/Mitigations:** API latency and rate limits → mitigate with batching, retries, and caching of embeddings.
* **Trade-offs:** Outsourcing embeddings improves quality but incurs cost and external dependency.
* **Alternatives Considered:** OpenAI, Cohere, local SentenceTransformers (cheaper but infra-heavy).

---

## Vector Database (Pinecone)

* **Design Decision:** Pinecone selected for vector similarity search. 
*Why:* Fully managed, scalable, with production-grade retrieval latencies.
* **Challenges/Mitigations:** Index scaling cost and query performance at large volumes → mitigate via namespace partitioning and dimension optimization.
* **Trade-offs:** Managed service reduces ops burden but locks into vendor pricing.
* **Alternatives Considered:** Weaviate (self-host), FAISS (in-house infra), Qdrant (open-source).

---

## Monitoring & Logging

* **Design Decision:** Centralized monitoring across ingestion and retrieval services. 
*Why:* Ensures reliability and observability in production.
* **Challenges/Mitigations:** Extra infra complexity → mitigate via container sidecars and standard metrics exporters.
* **Trade-offs:** Adds slight overhead to request paths but avoids blind spots in failures.
* **Alternatives Considered:** Prometheus/Grafana, DataDog, New Relic.

---

## Authentication Service

* **Design Decision:** API security enforced with token-based authentication. 
*Why:* Required for compliance and preventing unauthorized ingestion.
* **Challenges/Mitigations:** Latency overhead and token lifecycle management → mitigate with short-lived JWTs and gateway caching.
* **Trade-offs:** Stronger security vs. additional complexity for developers and ops.
* **Alternatives Considered:** OAuth2 providers, API Gateway native auth, mTLS.

---

## Production Considerations (Cross-Cutting)

* Load balancing for horizontal scale (why: distribute API load).
* Connection pooling for Postgres (why: avoid pool exhaustion).
* Async/await for I/O ops (why: maximize throughput per worker).
* Retry/backoff for embedding + Pinecone API calls (why: resiliency against transient errors).
* Containerized deployment with CI/CD (why: reproducibility and fast rollouts).
