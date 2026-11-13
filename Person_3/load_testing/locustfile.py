"""
locustfile.py — Locust Load Testing & Capacity Planning Suite (Unit 2.E)
Simulates concurrent complaint submissions, case queue inspection, and health auditing.
Measures P50, P95 latency percentiles, requests per second (RPS), and error rates.
"""

from __future__ import annotations

import random
from locust import HttpUser, task, between

SAMPLE_SCENARIOS = [
    {
        "complaint_text": "I did not make this ₹20,000 transaction. Please block and investigate.",
        "transaction_id": "TX1001",
    },
    {
        "complaint_text": "I was charged twice for the same restaurant meal.",
        "transaction_id": "TX1002",
    },
    {
        "complaint_text": "I paid for the items but they were never delivered.",
        "transaction_id": "TX1002",
    },
    {
        "complaint_text": "Incorrect billing amount charged on my credit statement.",
        "transaction_id": "TX1002",
    },
]


class DisputeCustomerUser(HttpUser):
    """Simulates cardholders actively submitting dispute complaints."""
    wait_time = between(0.5, 2.0)

    @task(5)
    def submit_dispute_complaint(self):
        scenario = random.choice(SAMPLE_SCENARIOS)
        headers = {"Content-Type": "application/json"}
        with self.client.post(
            "/api/v1/triage",
            json=scenario,
            headers=headers,
            catch_response=True,
            name="/api/v1/triage",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "case_id" in data and "priority" in data:
                    response.success()
                else:
                    response.failure("Malformed triage response")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")

    @task(2)
    def submit_async_dispute(self):
        scenario = random.choice(SAMPLE_SCENARIOS)
        self.client.post("/api/v1/async-triage", json=scenario, name="/api/v1/async-triage")


class CaseInvestigatorUser(HttpUser):
    """Simulates dispute operations officers reviewing and filtering cases."""
    wait_time = between(1.0, 3.0)

    @task(3)
    def list_review_queue(self):
        self.client.get("/api/v1/cases?status=under_review&limit=20", name="/api/v1/cases")

    @task(1)
    def check_system_health(self):
        self.client.get("/api/v1/health", name="/api/v1/health")

    @task(1)
    def check_sla_compliance(self):
        self.client.get("/api/v1/sla", name="/api/v1/sla")
