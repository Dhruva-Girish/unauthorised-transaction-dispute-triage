# Person 2 — AI Agent & Tool Integration Microservice
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="/app"

CMD ["python", "-c", "from agents.triage_agent import process_complaint; print('Person 2 Agent Engine Ready.')"]
