"""
Unit tests for Reliability Engineering modules: Circuit Breaker, Retries, and Graceful Degradation.
"""
import sys
from pathlib import Path
import pytest
import time

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))

try:
    from Person_3.reliability.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
    from Person_3.reliability.retry_handler import retry_with_backoff
    from Person_3.reliability.graceful_degradation import GracefulDegradationManager
except ImportError:
    from reliability.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
    from reliability.retry_handler import retry_with_backoff
    from reliability.graceful_degradation import GracefulDegradationManager

def test_circuit_breaker_transitions():
    cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=0.2)
    assert cb.state == "CLOSED"

    # Trip the breaker with failures
    def failing_call():
        raise ValueError("Service unavailable")

    with pytest.raises(ValueError):
        cb.call(failing_call)
    assert cb.state == "CLOSED"

    with pytest.raises(ValueError):
        cb.call(failing_call)
    assert cb.state == "OPEN"

    # Call while open should raise CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        cb.call(failing_call)

    # Wait for recovery timeout
    time.sleep(0.25)

    # In HALF-OPEN, successful call closes the circuit
    def successful_call():
        return "success"

    result = cb.call(successful_call)
    assert result == "success"
    assert cb.state == "CLOSED"

def test_retry_with_backoff_success():
    attempts = 0

    @retry_with_backoff(max_retries=3, initial_delay=0.01)
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise IOError("Transient network error")
        return "recovered"

    result = flaky_func()
    assert result == "recovered"
    assert attempts == 3

def test_graceful_degradation_llm_fallback():
    mgr = GracefulDegradationManager()
    
    # Simulate LLM call failing and engaging fallback
    def failing_llm():
        raise ConnectionError("Gemini LLM API timed out")

    result = mgr.execute_with_fallback(
        service_name="llm_service",
        primary_action=failing_llm,
        fallback_action=lambda: {"classification": "unauthorized_transaction", "source": "keyword_fallback"}
    )

    assert result["classification"] == "unauthorized_transaction"
    assert result["source"] == "keyword_fallback"
