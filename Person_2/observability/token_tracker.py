"""
token_tracker.py — LLM Token Usage, Cost Tracking & Latency Telemetry (Unit 3.H)
Calculates prompt and completion tokens, estimated USD/INR cost, and latency metrics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Pricing per 1M tokens (Gemini 2.5 Flash reference rate)
PROMPT_COST_PER_M = 0.075  # $0.075 per 1M input tokens
COMPLETION_COST_PER_M = 0.30  # $0.30 per 1M output tokens
USD_TO_INR = 86.50


@dataclass
class LLMExecutionMetrics:
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    cost_inr: float
    latency_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TokenCostTracker:
    """Tracks token consumption and API expenditures across agent sessions."""

    def __init__(self) -> None:
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0
        self.total_cost_inr = 0.0
        self.call_history: list[LLMExecutionMetrics] = []

    def record_call(
        self,
        model_name: str,
        prompt_text: str,
        completion_text: str,
        latency_ms: float,
    ) -> LLMExecutionMetrics:
        """Estimate tokens (approx 4 chars per token) and calculate billing cost."""
        p_tokens = max(1, len(prompt_text) // 4)
        c_tokens = max(1, len(completion_text) // 4)
        tot_tokens = p_tokens + c_tokens

        cost_usd = (p_tokens / 1_000_000 * PROMPT_COST_PER_M) + (c_tokens / 1_000_000 * COMPLETION_COST_PER_M)
        cost_inr = cost_usd * USD_TO_INR

        metric = LLMExecutionMetrics(
            model_name=model_name,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=tot_tokens,
            cost_usd=round(cost_usd, 7),
            cost_inr=round(cost_inr, 5),
            latency_ms=round(latency_ms, 2),
        )

        self.total_prompt_tokens += p_tokens
        self.total_completion_tokens += c_tokens
        self.total_cost_usd += cost_usd
        self.total_cost_inr += cost_inr
        self.call_history.append(metric)

        return metric

    def get_summary(self) -> dict[str, Any]:
        """Return aggregate token usage and cost metrics."""
        return {
            "total_calls": len(self.call_history),
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_cost_inr": round(self.total_cost_inr, 4),
            "average_latency_ms": round(
                sum(m.latency_ms for m in self.call_history) / len(self.call_history), 2
            ) if self.call_history else 0.0,
        }


# Global tracker
token_tracker = TokenCostTracker()
