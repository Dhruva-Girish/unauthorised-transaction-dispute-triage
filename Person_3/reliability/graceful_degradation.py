"""
graceful_degradation.py — Graceful Degradation & Fallback Manager (Unit 2.D)
Maintains safe continuous operation when external APIs, database, or ML endpoints degrade.
"""

from __future__ import annotations

from typing import Any
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

# Pre-configured breakers
gemini_breaker = CircuitBreaker("gemini_api", failure_threshold=3, recovery_timeout_sec=15.0)
ml_model_breaker = CircuitBreaker("ml_model_service", failure_threshold=4, recovery_timeout_sec=20.0)


class GracefulDegradationManager:
    """Orchestrates fallbacks during component outages."""

    @staticmethod
    def execute_with_fallback(
        service_name: str,
        primary_action,
        fallback_action,
        *args,
        **kwargs,
    ) -> Any:
        """Generic fallback execution guarded against exceptions."""
        try:
            return primary_action(*args, **kwargs)
        except Exception:
            return fallback_action(*args, **kwargs)

    @staticmethod
    def execute_with_gemini_fallback(gemini_fn, keyword_fallback_fn, *args, **kwargs) -> Any:
        """Call Gemini API via circuit breaker; fall back to keyword classifier on breaker open or exception."""
        try:
            return gemini_breaker.call(gemini_fn, *args, **kwargs)
        except (CircuitBreakerOpenException, Exception):
            return keyword_fallback_fn(*args, **kwargs)

    @staticmethod
    def execute_with_ml_fallback(ml_fn, default_unavailable_fn, *args, **kwargs) -> Any:
        """Call ML model via circuit breaker; fall back to safe unavailable result without inventing scores."""
        try:
            return ml_model_breaker.call(ml_fn, *args, **kwargs)
        except (CircuitBreakerOpenException, Exception):
            return default_unavailable_fn(*args, **kwargs)


degradation_manager = GracefulDegradationManager()
