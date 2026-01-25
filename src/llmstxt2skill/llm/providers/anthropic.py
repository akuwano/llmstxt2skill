"""Anthropic LLM provider."""

import os

import httpx

from llmstxt2skill.llm.base import LLMRequest


class AnthropicProvider:
    """LLM provider for Anthropic Messages API.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120,
    ) -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: API base URL (defaults to ANTHROPIC_BASE_URL or https://api.anthropic.com)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If api_key is not provided
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.base_url = (
            base_url
            or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        ).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

    async def generate(self, request: LLMRequest) -> str:
        """Generate text using Anthropic Messages API.

        Args:
            request: The LLM request parameters

        Returns:
            Generated text response

        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        body = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}],
        }

        if request.system:
            body["system"] = request.system

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

        # Anthropic returns content as list of blocks
        parts = [
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        return "".join(parts).strip()
