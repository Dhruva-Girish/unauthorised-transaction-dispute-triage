"""
rate_limiter.py — Token Bucket Rate Limiter (Unit 2.F)
Protects API endpoints from request flooding and denial of service attacks.
"""

from __future__ import annotations

import time
from threading import Lock
from fastapi import Request, HTTPException, status


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket Rate Limiter per client IP."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_limit: int = 20,
        rate: float | None = None,
        capacity: float | None = None,
    ) -> None:
        self.capacity = float(capacity) if capacity is not None else float(burst_limit)
        self.fill_rate = float(rate) if rate is not None else (requests_per_minute / 60.0)
        self.tokens: dict[str, float] = {}
        self.last_update: dict[str, float] = {}
        self._lock = Lock()

    def check_rate_limit(self, client_id: str) -> bool:
        """Return True if request is allowed, False if rate limit exceeded."""
        now = time.time()

        with self._lock:
            if client_id not in self.tokens:
                self.tokens[client_id] = self.capacity
                self.last_update[client_id] = now

            # Replenish tokens based on elapsed time
            elapsed = now - self.last_update[client_id]
            self.tokens[client_id] = min(self.capacity, self.tokens[client_id] + elapsed * self.fill_rate)
            self.last_update[client_id] = now

            if self.tokens[client_id] >= 1.0:
                self.tokens[client_id] -= 1.0
                return True
            return False

    allow_request = check_rate_limit


# Global rate limiter (default 120 req/min with burst of 30)
rate_limiter = TokenBucketRateLimiter(requests_per_minute=120, burst_limit=30)


async def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency enforcing client IP rate limits."""
    client_ip = request.client.host if request.client else "unknown_client"
    if not rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests. Please slow down.",
        )
