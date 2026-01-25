"""Databricks LLM provider."""

import os

import httpx

from llmstxt2skill.llm.base import LLMRequest


class DatabricksProvider:
    """LLM provider for Databricks Model Serving endpoints.

    Requires DATABRICKS_HOST and DATABRICKS_TOKEN environment variables.
    """

    def __init__(
        self,
        host: str | None = None,
        token: str | None = None,
        timeout: float = 120,
    ) -> None:
        """Initialize Databricks provider.

        Args:
            host: Databricks workspace URL (defaults to DATABRICKS_HOST env var)
            token: Databricks access token (defaults to DATABRICKS_TOKEN env var)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If host or token is not provided
        """
        self.host = (host or os.environ.get("DATABRICKS_HOST", "")).rstrip("/")
        self.token = token or os.environ.get("DATABRICKS_TOKEN", "")
        self.timeout = timeout

        if not self.host or not self.token:
            raise ValueError(
                "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables must be set"
            )

    async def generate(self, request: LLMRequest) -> str:
        """Generate text using Databricks Model Serving.

        Args:
            request: The LLM request parameters

        Returns:
            Generated text response

        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.host}/serving-endpoints/{request.model}/invocations"

        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        # Handle response formats where content is a list
        if isinstance(content, list):
            content = content[0].get("text", str(content[0]))
        return content
