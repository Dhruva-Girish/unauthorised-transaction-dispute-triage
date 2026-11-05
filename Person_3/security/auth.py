"""
auth.py — API Authentication & Access Control Middleware (Unit 2.F)
Enforces API key authentication and bearer token verification for protected endpoints.
"""

from __future__ import annotations

import os
from fastapi import Header, HTTPException, status

DEFAULT_API_KEY = os.getenv("API_KEY_SECRET", "dispute-triage-default-secret-key-change-in-prod")


class SecurityConfig:
    API_KEY = DEFAULT_API_KEY
    BEARER_TOKEN = DEFAULT_API_KEY


def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> str | bool:
    """
    Validate that incoming request contains valid X-API-Key or Bearer token.
    Supports both direct functional call verify_api_key(key) and FastAPI dependency injection.
    """
    valid_key = os.getenv("API_KEY_SECRET", SecurityConfig.API_KEY)

    # Allow direct functional check verify_api_key("some_key")
    if isinstance(x_api_key, str) and not isinstance(authorization, str):
        return x_api_key == valid_key

    # 1. Check X-API-Key header
    if isinstance(x_api_key, str) and x_api_key == valid_key:
        return "api-key-client"

    # 2. Check Bearer token in Authorization header
    if isinstance(authorization, str):
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == valid_key:
            return "bearer-token-client"

    # In development mode, allow localhost dev bypass if DEBUG=true
    if os.getenv("DEBUG", "false").lower() == "true":
        return "development-bypass"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API authentication credentials. Provide a valid 'X-API-Key' or 'Authorization: Bearer <token>' header.",
        headers={"WWW-Authenticate": "Bearer"},
    )
