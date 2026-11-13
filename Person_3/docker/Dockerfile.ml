# Dockerfile for Person 1 ML Inference Service
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY Person_1/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and contracts
COPY shared_contracts/ /app/shared_contracts/
COPY Person_1/ /app/Person_1/

ENV PYTHONPATH="/app:/app/Person_1:/app/shared_contracts"
ENV PORT=8001

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "-m", "uvicorn", "Person_1.serving.prediction_service:app", "--host", "0.0.0.0", "--port", "8001"]
