"""Tests for CLI."""

import sys
from unittest.mock import AsyncMock, patch

import pytest

from llmstxt2skill.cli import main, parse_args


class TestParseArgs:
    def test_url_required(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_url_only(self):
        args = parse_args(["https://example.com/llms.txt"])
        assert args.url == "https://example.com/llms.txt"
        assert args.name is None
        assert args.output is None
        assert args.dry_run is False
        assert args.force is False

    def test_with_output(self):
        args = parse_args(["https://example.com/llms.txt", "--output", "/custom/path"])
        assert args.output == "/custom/path"

    def test_with_output_short(self):
        args = parse_args(["https://example.com/llms.txt", "-o", "/custom/path"])
        assert args.output == "/custom/path"

    def test_with_name(self):
        args = parse_args(["https://example.com/llms.txt", "--name", "my-skill"])
        assert args.name == "my-skill"

    def test_dry_run(self):
        args = parse_args(["https://example.com/llms.txt", "--dry-run"])
        assert args.dry_run is True

    def test_force(self):
        args = parse_args(["https://example.com/llms.txt", "--force"])
        assert args.force is True

    def test_all_options(self):
        args = parse_args([
            "https://example.com/llms.txt",
            "--name", "custom",
            "--dry-run",
            "--force",
        ])
        assert args.url == "https://example.com/llms.txt"
        assert args.name == "custom"
        assert args.dry_run is True
        assert args.force is True


class TestMain:
    @pytest.mark.asyncio
    async def test_main_dry_run(self, capsys):
        llmstxt_content = """# Test Docs

> Test description.

## Section
- [Link](https://example.com)
"""
        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = llmstxt_content

            argv = ["llmstxt2skill", "https://example.com/llms.txt", "--dry-run"]
            with patch.object(sys, "argv", argv):
                await main()

        captured = capsys.readouterr()
        assert "test-docs" in captured.out.lower() or "Test Docs" in captured.out

    @pytest.mark.asyncio
    async def test_main_writes_file(self, tmp_path):
        llmstxt_content = """# Test Docs

> Test description.

## Section
- [Link](https://example.com)
"""
        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = llmstxt_content

            with patch("llmstxt2skill.cli.get_default_base_path", return_value=tmp_path):
                with patch.object(sys, "argv", ["llmstxt2skill", "https://example.com/llms.txt"]):
                    await main()

        skill_file = tmp_path / "test-docs" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "name: test-docs" in content

    @pytest.mark.asyncio
    async def test_main_with_custom_output(self, tmp_path):
        llmstxt_content = """# Test Docs

> Test description.

## Section
- [Link](https://example.com)
"""
        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = llmstxt_content

            argv = [
                "llmstxt2skill",
                "https://example.com/llms.txt",
                "--output", str(tmp_path),
            ]
            with patch.object(sys, "argv", argv):
                await main()

        skill_file = tmp_path / "test-docs" / "SKILL.md"
        assert skill_file.exists()
