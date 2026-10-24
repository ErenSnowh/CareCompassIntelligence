# CareCompass AI — Production Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and dataset
COPY backend/app /app/app
COPY caregivers.csv /app/caregivers.csv
COPY triage_dataset.jsonl /app/triage_dataset.jsonl

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production

EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
