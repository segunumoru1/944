FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pandas/numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Use different commands for dev vs prod (remove --reload for prod)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]