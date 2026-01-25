"""OpenAI-compatible LLM provider for local LLMs."""

import os

import httpx

from llmstxt2skill.llm.base import LLMRequest


class OpenAICompatibleProvider:
    """LLM provider for OpenAI-compatible APIs (vLLM, llama.cpp, Ollama, etc.).

    Uses the same API format as OpenAI but with relaxed authentication
    requirements for local deployments.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 120,
    ) -> None:
        """Initialize OpenAI-compatible provider.

        Args:
            base_url: API base URL (defaults to OPENAI_BASE_URL or http://localhost:8000)
            api_key: Optional API key (defaults to OPENAI_API_KEY, can be empty)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If base_url is not provided
        """
        self.base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL", "http://localhost:8000")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout

        if not self.base_url:
            raise ValueError(
                "base_url or OPENAI_BASE_URL environment variable must be set"
            )

    async def generate(self, request: LLMRequest) -> str:
        """Generate text using OpenAI-compatible API.

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

        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=headers,
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
