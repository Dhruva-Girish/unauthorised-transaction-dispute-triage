"""
gemini_provider.py — Google Gemini LLM Provider (Unit 3.G)
"""

from __future__ import annotations

import os
from typing import Any
from .provider_factory import BaseLLMProvider

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider implementation."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None) -> None:
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def is_available(self) -> bool:
        return GENAI_AVAILABLE and bool(self.api_key)

    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> str:
        if not self.is_available():
            raise RuntimeError("GeminiProvider unavailable: missing GEMINI_API_KEY or google-genai package.")

        client = genai.Client(api_key=self.api_key)
        config: dict[str, Any] = {}
        if schema:
            config["response_mime_type"] = "application/json"
            config["response_json_schema"] = schema

        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config if config else None,
        )
        return response.text or ""
