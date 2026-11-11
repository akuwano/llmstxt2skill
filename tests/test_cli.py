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

    def test_update(self):
        args = parse_args(["https://example.com/llms.txt", "--update"])
        assert args.update is True

    def test_update_default_false(self):
        args = parse_args(["https://example.com/llms.txt"])
        assert args.update is False

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

    def test_local_path(self):
        args = parse_args(["./llms.txt", "--dry-run"])
        assert args.url == "./llms.txt"
        assert args.dry_run is True


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

    @pytest.mark.asyncio
    async def test_main_update_shows_diff_and_overwrites(self, tmp_path, capsys):
        old_content = """# Test Docs

## Section
- [Old](https://example.com/old)
"""
        new_content = """# Test Docs

## Section
- [New](https://example.com/new)
"""
        skill_file = tmp_path / "test-docs" / "SKILL.md"
        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = old_content
            with patch.object(sys, "argv", ["llmstxt2skill", "https://example.com/llms.txt",
                                            "-o", str(tmp_path)]):
                await main()

            mock_fetch.return_value = new_content
            with patch.object(sys, "argv", ["llmstxt2skill", "https://example.com/llms.txt",
                                            "-o", str(tmp_path), "--update"]):
                await main()

        captured = capsys.readouterr()
        assert "+ [New](https://example.com/new)" in captured.out
        assert "- [Old](https://example.com/old)" in captured.out
        assert f"Updated: {skill_file}" in captured.out
        assert "https://example.com/new" in skill_file.read_text()

    @pytest.mark.asyncio
    async def test_main_update_missing_skill_exits_before_enrich(self, tmp_path, capsys):
        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "# Test Docs\n"
            with patch("llmstxt2skill.enricher.enrich_skill", new_callable=AsyncMock) as enrich:
                argv = ["llmstxt2skill", "https://example.com/llms.txt",
                        "-o", str(tmp_path), "--update", "--enrich"]
                with patch.object(sys, "argv", argv):
                    with pytest.raises(SystemExit) as exc:
                        await main()

        assert exc.value.code == 1
        enrich.assert_not_called()
        captured = capsys.readouterr()
        assert "Skill not found:" in captured.err

    @pytest.mark.asyncio
    async def test_main_update_unreadable_skill_exits_with_error(self, tmp_path, capsys):
        # SKILL.md is a directory, so reading it fails
        (tmp_path / "test-docs" / "SKILL.md").mkdir(parents=True)
        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "# Test Docs\n"
            argv = ["llmstxt2skill", "https://example.com/llms.txt",
                    "-o", str(tmp_path), "--update"]
            with patch.object(sys, "argv", argv):
                with pytest.raises(SystemExit) as exc:
                    await main()

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Cannot read existing skill:" in captured.err
        assert "Traceback" not in captured.err

    @pytest.mark.asyncio
    async def test_main_reads_local_file(self, tmp_path, capsys):
        llms_file = tmp_path / "llms.txt"
        llms_file.write_text("""# Local Docs

> Local description.

## Section
- [Link](https://example.com/local)
""", encoding="utf-8")

        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            argv = ["llmstxt2skill", str(llms_file), "--dry-run"]
            with patch.object(sys, "argv", argv):
                await main()

        mock_fetch.assert_not_called()
        captured = capsys.readouterr()
        assert f"Reading {llms_file}..." in captured.out
        assert "name: local-docs" in captured.out
        assert "https://example.com/local" in captured.out

    @pytest.mark.asyncio
    async def test_main_missing_local_file_exits(self, tmp_path, capsys):
        missing = tmp_path / "missing.txt"

        with patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as mock_fetch:
            argv = ["llmstxt2skill", str(missing), "--dry-run"]
            with patch.object(sys, "argv", argv):
                with pytest.raises(SystemExit) as exc_info:
                    await main()

        assert exc_info.value.code == 1
        mock_fetch.assert_not_called()
        captured = capsys.readouterr()
        assert f"Error: Cannot read {missing}:" in captured.err


@pytest.mark.asyncio
async def test_main_update_with_local_file(tmp_path, capsys):
    """--update（#2）とローカルの llms.txt（#1）の組み合わせ。"""
    llms = tmp_path / "llms.txt"
    out = tmp_path / "skills"
    old = "# Local Docs\n\n## Section\n- [Old](https://example.com/old)\n"
    llms.write_text(old, encoding="utf-8")
    with patch.object(sys, "argv", ["llmstxt2skill", str(llms), "-o", str(out)]):
        await main()
    new = "# Local Docs\n\n## Section\n- [New](https://example.com/new)\n"
    llms.write_text(new, encoding="utf-8")
    with patch.object(sys, "argv", ["llmstxt2skill", str(llms), "-o", str(out), "--update"]):
        await main()
    captured = capsys.readouterr()
    assert "+ [New](https://example.com/new)" in captured.out
    assert "- [Old](https://example.com/old)" in captured.out
    assert "https://example.com/new" in (out / "local-docs" / "SKILL.md").read_text()
