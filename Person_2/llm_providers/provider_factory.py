"""
provider_factory.py — Configurable LLM Provider Interface & Factory (Unit 3.G)
Decouples application agents from specific LLM providers.
Supports Google Gemini, Local LLMs (Ollama/HuggingFace), and Rule-based local engines.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract interface for all language model providers."""

    @abstractmethod
    def generate(self, prompt: str, schema: dict[str, Any] | None = None) -> str:
        """Generate text or structured response from the LLM."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check provider health and credentials availability."""
        pass


def get_llm_provider(provider_type: str | None = None) -> BaseLLMProvider:
    """Factory creating the configured LLM provider instance."""
    p_type = (provider_type or os.getenv("LLM_PROVIDER", "gemini")).lower()

    if p_type == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider()
    elif p_type in ("local", "ollama", "huggingface"):
        from .local_provider import LocalLLMProvider
        return LocalLLMProvider()
    else:
        from .local_provider import LocalLLMProvider
        return LocalLLMProvider()
