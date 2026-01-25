"""Tests for URL fetcher."""

import pytest

from llmstxt2skill.fetcher import fetch_llmstxt


class TestFetchLlmstxt:
    @pytest.mark.asyncio
    async def test_fetch_valid_url(self, httpx_mock):
        """Test fetching from a valid URL."""
        httpx_mock.add_response(
            url="https://example.com/llms.txt",
            text="# Example Docs\n\n> Description\n",
        )

        content = await fetch_llmstxt("https://example.com/llms.txt")
        assert "# Example Docs" in content

    @pytest.mark.asyncio
    async def test_fetch_404_raises_error(self, httpx_mock):
        """Test that 404 raises an error."""
        httpx_mock.add_response(
            url="https://example.com/llms.txt",
            status_code=404,
        )

        with pytest.raises(RuntimeError, match="Failed to fetch"):
            await fetch_llmstxt("https://example.com/llms.txt")

    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self):
        """Test that invalid URL raises an error."""
        with pytest.raises(RuntimeError):
            await fetch_llmstxt("not-a-valid-url")
