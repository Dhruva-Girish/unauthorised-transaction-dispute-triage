"""
local_provider.py — Self-Hosted / Local LLM Provider (Unit 3.G)
Supports local Ollama / HuggingFace endpoints or local deterministic fallback.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .provider_factory import BaseLLMProvider


class LocalLLMProvider(BaseLLMProvider):
    """Local LLM Provider communicating with Ollama or local inference endpoint."""

    def __init__(self, endpoint_url: str | None = None, model: str = "llama3:latest") -> None:
        self.endpoint_url = endpoint_url or os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
        self.model = model

    def is_available(self) -> bool:
        """Ping local Ollama /api/tags endpoint to check if service is up."""
        try:
            req = urllib.request.Request(f"{self.endpoint_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> str:
        """Call local LLM API with deterministic structured fallback if offline."""
        if self.is_available():
            try:
                payload = json.dumps({
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json" if schema else "",
                }).encode("utf-8")

                req = urllib.request.Request(
                    f"{self.endpoint_url}/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("response", "")
            except Exception:
                pass

        # Offline Local Engine: deterministic synthesis based on prompt contents
        if "Choose exactly one category" in prompt:
            # Deterministic classification logic
            try:
                from classification.keyword_fallback import KeywordFallbackClassifier
            except ImportError:
                from Person_2.classification.keyword_fallback import KeywordFallbackClassifier
            category = KeywordFallbackClassifier.classify_text(prompt)
            return json.dumps({"complaint_category": category, "confidence": 0.88})

        return json.dumps({
            "analysis": "Local rule-based inference completed.",
            "status": "under_review",
            "priority": "review_required",
        })
