"""Base interfaces for LLM providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    """Request object for LLM generation.

    Attributes:
        prompt: The user prompt to send
        model: Model identifier (provider-specific)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)
        system: Optional system prompt
    """

    prompt: str
    model: str
    max_tokens: int = 4000
    temperature: float = 0.2
    system: str | None = None


class LLMProvider(Protocol):
    """Protocol for LLM providers.

    Implementations must provide an async generate method that takes
    an LLMRequest and returns the generated text.
    """

    async def generate(self, request: LLMRequest) -> str:
        """Generate text from the LLM.

        Args:
            request: The LLM request parameters

        Returns:
            Generated text response
        """
        ...
