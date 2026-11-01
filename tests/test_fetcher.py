"""Tests for llms.txt fetcher and local file reader."""

import pytest

from llmstxt2skill.fetcher import fetch_llmstxt, is_url, read_llmstxt_file


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


class TestIsUrl:
    @pytest.mark.parametrize("source", [
        "https://example.com/llms.txt",
        "http://example.com/llms.txt",
        "HTTPS://example.com/llms.txt",
    ])
    def test_http_schemes_are_urls(self, source):
        assert is_url(source) is True

    @pytest.mark.parametrize("source", [
        "./llms.txt",
        "llms.txt",
        "/abs/path/llms.txt",
        "example.com/llms.txt",
    ])
    def test_paths_are_not_urls(self, source):
        assert is_url(source) is False


class TestReadLlmstxtFile:
    def test_read_file(self, tmp_path):
        path = tmp_path / "llms.txt"
        path.write_text("# Local Docs\n\n> 説明\n", encoding="utf-8")

        assert read_llmstxt_file(str(path)) == "# Local Docs\n\n> 説明\n"

    def test_read_file_strips_bom(self, tmp_path):
        path = tmp_path / "llms.txt"
        path.write_bytes("\ufeff# Local Docs\n".encode("utf-8"))

        assert read_llmstxt_file(path) == "# Local Docs\n"

    def test_missing_file_raises_value_error(self, tmp_path):
        path = tmp_path / "missing.txt"

        with pytest.raises(ValueError, match=f"Cannot read {path}:"):
            read_llmstxt_file(str(path))

    def test_directory_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="Cannot read"):
            read_llmstxt_file(str(tmp_path))

    def test_non_utf8_raises_value_error(self, tmp_path):
        path = tmp_path / "llms.txt"
        path.write_bytes(b"# Docs \xff\xfe\n")

        with pytest.raises(ValueError, match="Cannot read"):
            read_llmstxt_file(str(path))
