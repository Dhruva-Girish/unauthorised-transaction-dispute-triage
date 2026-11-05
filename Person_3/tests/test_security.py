"""
Unit tests for Security modules: Authentication and Token Bucket Rate Limiting.
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
    from Person_3.security.auth import verify_api_key, SecurityConfig
    from Person_3.security.rate_limiter import TokenBucketRateLimiter
except ImportError:
    from security.auth import verify_api_key, SecurityConfig
    from security.rate_limiter import TokenBucketRateLimiter

def test_auth_verification():
    # Valid key
    assert bool(verify_api_key(SecurityConfig.API_KEY)) is True
    # Invalid key
    assert verify_api_key("wrong_token_xyz") is False
    # Empty key
    assert verify_api_key("") is False

def test_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(rate=5, capacity=5)
    client_ip = "192.168.1.10"

    # First 5 calls must be allowed
    for _ in range(5):
        assert limiter.allow_request(client_ip) is True

    # 6th call exceeds burst capacity
    assert limiter.allow_request(client_ip) is False

    # Wait for token refill (rate = 5 tokens/sec => 0.25 sec adds 1.25 tokens)
    time.sleep(0.3)
    assert limiter.allow_request(client_ip) is True
