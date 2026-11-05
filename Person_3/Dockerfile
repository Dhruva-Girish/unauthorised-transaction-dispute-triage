# Standalone Dockerfile for Person 3
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/Person_3/

ENV PYTHONPATH="/app:/app/Person_3"
ENV PORT=8000
ENV GRPC_PORT=50051

EXPOSE 8000 50051 8501

CMD ["python", "-m", "uvicorn", "Person_3.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
