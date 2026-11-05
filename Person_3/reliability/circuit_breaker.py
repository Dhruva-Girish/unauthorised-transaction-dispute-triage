"""
circuit_breaker.py — Circuit Breaker Pattern for External Dependencies (Unit 2.D)
Protects the application from cascading failures when Gemini API, database,
or model microservices experience elevated error rates.
"""

from __future__ import annotations

import time
from typing import Callable, Any


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is rejected by an OPEN circuit breaker."""
    pass


class CircuitBreaker:
    """
    Stateful circuit breaker with CLOSED, OPEN, and HALF-OPEN transitions.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        name: str = "default_breaker",
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        recovery_timeout: float | None = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout if recovery_timeout is not None else recovery_timeout_sec

        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count_half_open = 0

    def reset(self) -> None:
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count_half_open = 0

    def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute callable protected by the circuit breaker."""
        now = time.time()

        if self.state == self.OPEN:
            if now - self.last_failure_time > self.recovery_timeout_sec:
                self.state = self.HALF_OPEN
                self.success_count_half_open = 0
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN. Operation short-circuited."
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise exc

    def _on_success(self) -> None:
        if self.state == self.HALF_OPEN:
            self.success_count_half_open += 1
            if self.success_count_half_open >= 1:
                self.state = self.CLOSED
                self.failure_count = 0
        elif self.state == self.CLOSED:
            self.failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state in (self.CLOSED, self.HALF_OPEN) and self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
        }


# Global circuit breaker instances
gemini_breaker = CircuitBreaker(name="gemini_api", failure_threshold=3, recovery_timeout_sec=30.0)
ml_model_breaker = CircuitBreaker(name="ml_model_service", failure_threshold=3, recovery_timeout_sec=15.0)

_breakers = {
    "gemini": gemini_breaker,
    "llm": gemini_breaker,
    "ml": ml_model_breaker,
    "ml_model": ml_model_breaker,
}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name)
    return _breakers[name]
