"""
retry_handler.py — Exponential Backoff & Jitter Retry Utility (Unit 2.D)
Retries transient failures with configurable exponential delays and jitter.
Supports both functional invocation and decorator syntax.
"""

from __future__ import annotations

import functools
import random
import time
from typing import Callable, Any, Tuple, Type


def retry_with_backoff(
    func: Callable[..., Any] | None = None,
    max_retries: int | None = None,
    max_attempts: int = 3,
    initial_delay: float | None = None,
    initial_delay_sec: float = 0.2,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Any:
    """Execute a function with exponential backoff and jitter, or wrap as a decorator."""
    actual_attempts = max_retries if max_retries is not None else max_attempts
    actual_delay = initial_delay if initial_delay is not None else initial_delay_sec

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            delay = actual_delay
            last_exc = None

            for attempt in range(1, actual_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except retry_exceptions as exc:
                    last_exc = exc
                    if attempt == actual_attempts:
                        break
                    sleep_time = delay
                    if jitter:
                        sleep_time += random.uniform(0, 0.1 * delay)
                    time.sleep(sleep_time)
                    delay *= backoff_factor

            raise last_exc

        return wrapper

    if func is not None and callable(func):
        return decorator(func)()
    return decorator
