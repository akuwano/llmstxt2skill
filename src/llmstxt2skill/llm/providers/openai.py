"""OpenAI LLM provider."""

import os

import httpx

from llmstxt2skill.llm.base import LLMRequest


class OpenAIProvider:
    """LLM provider for OpenAI Chat Completions API.

    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120,
    ) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: API base URL (defaults to OPENAI_BASE_URL or https://api.openai.com)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If api_key is not provided
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
        ).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")

    async def generate(self, request: LLMRequest) -> str:
        """Generate text using OpenAI Chat Completions API.

        Args:
            request: The LLM request parameters

        Returns:
            Generated text response

        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/v1/chat/completions"

        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": request.model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]
