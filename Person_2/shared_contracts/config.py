"""
config.py — Centralized External Configuration Management
"""

import os
from functools import lru_cache
from pydantic import BaseModel, Field


class SystemSettings(BaseModel):
    """Application-wide configuration parameters."""
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # LLM Settings
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model_name: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"))
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini"))
    local_llm_url: str = Field(default_factory=lambda: os.getenv("LOCAL_LLM_URL", "http://localhost:11434"))
    
    # Service Endpoints
    fastapi_host: str = Field(default_factory=lambda: os.getenv("FASTAPI_HOST", "0.0.0.0"))
    fastapi_port: int = Field(default_factory=lambda: int(os.getenv("FASTAPI_PORT", "8000")))
    grpc_port: int = Field(default_factory=lambda: int(os.getenv("GRPC_PORT", "50051")))
    ml_service_url: str = Field(default_factory=lambda: os.getenv("ML_SERVICE_URL", "http://localhost:8001"))
    
    # Security
    api_key_secret: str = Field(default_factory=lambda: os.getenv("API_KEY_SECRET", "dispute-triage-default-secret-key-change-in-prod"))
    rate_limit_per_minute: int = Field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")))
    
    # Reliability & SLA
    sla_latency_threshold_ms: float = Field(default_factory=lambda: float(os.getenv("SLA_LATENCY_THRESHOLD_MS", "500.0")))
    circuit_breaker_max_failures: int = Field(default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_MAX_FAILURES", "5")))
    circuit_breaker_reset_timeout_sec: float = Field(default_factory=lambda: float(os.getenv("CIRCUIT_BREAKER_RESET_TIMEOUT_SEC", "30.0")))
    retry_max_attempts: int = Field(default_factory=lambda: int(os.getenv("RETRY_MAX_ATTEMPTS", "3")))
    
    # Storage Paths
    data_dir: str = Field(default_factory=lambda: os.getenv("DATA_DIR", "data"))
    logs_dir: str = Field(default_factory=lambda: os.getenv("LOGS_DIR", "logs"))


@lru_cache(maxsize=1)
def get_settings() -> SystemSettings:
    """Return cached singleton instance of SystemSettings."""
    return SystemSettings()
