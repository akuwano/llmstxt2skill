"""--update の受け入れテスト。ネットワークと LLM の応答だけを差し替える。"""

import sys
from unittest.mock import AsyncMock, patch

import pytest

from llmstxt2skill.cli import main


URL = "https://example.com/llms.txt"
OLD = """# Update Docs

> Documentation index.

## Guides
- [A](https://example.com/a)
- [B](https://example.com/b)

## Legacy
- [Old](https://example.com/old)
"""
NEW = """# Update Docs

> Documentation index.

## Guides
- [A](https://example.com/a)
- [C](https://example.com/c)

## API
- [API Ref](https://example.com/api)
"""
EXPECTED_DIFF = [
    "+ API",
    "- Legacy",
    "+ [C](https://example.com/c)",
    "+ [API Ref](https://example.com/api)",
    "- [B](https://example.com/b)",
    "- [Old](https://example.com/old)",
]
OLD_RESPONSE = """# ローカライズされたガイド

既存の説明。

## ガイド
| 文書 | 説明 |
| --- | --- |
| [旧A](https://example.com/a) | 継続 |
| [旧B](https://example.com/b) | 削除対象 |
"""
NEW_RESPONSE = """# ローカライズされたガイド

新しい説明。

## ガイド
| 文書 | 説明 |
| --- | --- |
| [新A](https://example.com/a) | 継続 |
| [新C](https://example.com/c) | 追加対象 |
"""


def diff_lines(stdout):
    return [
        line.strip()
        for line in stdout.splitlines()
        if line.strip().startswith(("+ ", "- "))
    ]


@pytest.fixture
def invoke(capsys):
    async def call(content, output, *options, response=None):
        provider = AsyncMock()
        provider.generate.return_value = response or NEW_RESPONSE
        argv = ["llmstxt2skill", URL, "-o", str(output), *options]
        with (
            patch.object(sys, "argv", argv),
            patch("llmstxt2skill.cli.fetch_llmstxt", new_callable=AsyncMock) as fetch,
            patch("llmstxt2skill.enricher.create_provider", return_value=provider),
        ):
            fetch.return_value = content
            code = 0
            try:
                await main()
            except SystemExit as exc:
                code = exc.code
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return call


@pytest.fixture
async def existing(invoke, tmp_path):
    base = tmp_path / "skills"
    code, out, err = await invoke(OLD, base)
    assert code == 0, (out, err)
    path = base / "update-docs" / "SKILL.md"
    assert path.is_file()
    return base, path


@pytest.mark.asyncio
async def test_ac1_update_reports_changes_and_matches_fresh_creation(invoke, existing, tmp_path):
    """AC-1: 増減だけを表示し、新規生成と同じ内容で上書きする。"""
    base, path = existing
    before = path.read_bytes()
    code, out, err = await invoke(NEW, base, "--update")

    assert code == 0, (out, err)
    assert diff_lines(out) == EXPECTED_DIFF
    assert f"Updated: {path}" in out.splitlines()
    for heading in (
        "Sections added (1):",
        "Sections removed (1):",
        "Links added (2):",
        "Links removed (2):",
    ):
        assert heading in out
    assert path.read_bytes() != before

    fresh = tmp_path / "fresh"
    fresh_code, fresh_out, fresh_err = await invoke(NEW, fresh)
    assert fresh_code == 0, (fresh_out, fresh_err)
    assert path.read_bytes() == (fresh / "update-docs" / "SKILL.md").read_bytes()


@pytest.mark.asyncio
async def test_ac2_identical_source_reports_no_changes(invoke, existing):
    """AC-2: 同じ入力でも更新成功を通知し、差分の行を出さない。"""
    base, path = existing
    before = path.read_bytes()
    code, out, err = await invoke(OLD, base, "--update")

    assert code == 0, (out, err)
    assert "No changes in sections or links." in out.splitlines()
    assert diff_lines(out) == []
    assert f"Updated: {path}" in out.splitlines()
    assert path.read_bytes() == before


@pytest.mark.asyncio
async def test_ac2_link_title_changes_do_not_count_as_url_changes(invoke, existing):
    """AC-2: URL が同じならタイトルだけの変更を増減として表示しない。"""
    base, path = existing
    renamed = OLD.replace("[A]", "[Renamed A]")
    code, out, err = await invoke(renamed, base, "--update")

    assert code == 0, (out, err)
    assert "No changes in sections or links." in out.splitlines()
    assert diff_lines(out) == []
    assert f"Updated: {path}" in out.splitlines()
    assert "[Renamed A](https://example.com/a)" in path.read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize("custom_name", [None, "custom-docs"])
async def test_ac3_missing_skill_is_an_error(invoke, tmp_path, custom_name):
    """AC-3: 既定名・指定名のどちらでも、存在しない対象を新規作成しない。"""
    base = tmp_path / "missing"
    name = custom_name or "update-docs"
    options = ["--update"]
    if custom_name:
        options.extend(["--name", custom_name])
    path = base / name / "SKILL.md"

    code, out, err = await invoke(NEW, base, *options)

    assert code == 1, (out, err)
    assert "Skill not found:" in err
    assert str(path) in err
    assert "Run without --update to create it" in err
    assert not path.exists()
    assert not list(base.rglob("SKILL.md"))
    assert "Updated:" not in out


@pytest.mark.asyncio
async def test_ac4_update_dry_run_only_reports_changes(invoke, existing):
    """AC-4: 差分は表示するが、本文も更新完了通知も出さず、書き換えない。"""
    base, path = existing
    before = path.read_bytes()
    code, out, err = await invoke(NEW, base, "--update", "--dry-run")

    assert code == 0, (out, err)
    assert diff_lines(out) == EXPECTED_DIFF
    assert path.read_bytes() == before
    assert "Updated:" not in out
    assert "--- SKILL.md (dry-run) ---" not in out
    assert "# Update Docs" not in out
    assert "name: update-docs" not in out


@pytest.mark.asyncio
async def test_ac5_enriched_update_compares_generated_markdown(invoke, tmp_path):
    """AC-5: 入力 llms.txt でなく、LLM 応答から作った本文のリンクを比較する。"""
    base = tmp_path / "enriched"
    options = ("--enrich", "--provider", "openai-compatible", "--model", "test-model")
    code, out, err = await invoke(OLD, base, *options, response=OLD_RESPONSE)
    assert code == 0, (out, err)
    path = base / "update-docs" / "SKILL.md"
    assert "[旧B](https://example.com/b)" in path.read_text(encoding="utf-8")

    # 入力は変えず、差し替えた LLM 応答だけを変更する。
    code, out, err = await invoke(
        OLD, base, *options, "--update", response=NEW_RESPONSE
    )

    assert code == 0, (out, err)
    assert diff_lines(out) == [
        "+ [新C](https://example.com/c)",
        "- [旧B](https://example.com/b)",
    ]
    assert f"Updated: {path}" in out.splitlines()
    markdown = path.read_text(encoding="utf-8")
    assert NEW_RESPONSE.strip() in markdown
    assert "https://example.com/b" not in markdown

    fresh = tmp_path / "fresh-enriched"
    fresh_code, fresh_out, fresh_err = await invoke(
        OLD, fresh, *options, response=NEW_RESPONSE
    )
    assert fresh_code == 0, (fresh_out, fresh_err)
    assert path.read_bytes() == (fresh / "update-docs" / "SKILL.md").read_bytes()


@pytest.mark.asyncio
async def test_ac6_existing_skill_without_flags_is_preserved(invoke, existing):
    """AC-6: --update も --force も無ければ既存ファイルを保護する。"""
    base, path = existing
    before = path.read_bytes()
    code, out, err = await invoke(NEW, base)

    assert code == 1, (out, err)
    assert "Use --force to overwrite" in err
    assert path.read_bytes() == before


@pytest.mark.asyncio
async def test_ac6_force_overwrites_without_diff(invoke, existing, tmp_path):
    """AC-6: --force は引き続き差分を表示せずに上書きする。"""
    base, path = existing
    before = path.read_bytes()
    code, out, err = await invoke(NEW, base, "--force")

    assert code == 0, (out, err)
    assert diff_lines(out) == []
    assert path.read_bytes() != before
    fresh = tmp_path / "fresh-force-reference"
    fresh_code, fresh_out, fresh_err = await invoke(NEW, fresh)
    assert fresh_code == 0, (fresh_out, fresh_err)
    assert path.read_bytes() == (fresh / "update-docs" / "SKILL.md").read_bytes()


@pytest.mark.asyncio
async def test_ac6_new_skill_without_update_is_created(invoke, tmp_path):
    """AC-6: --update 無しの新規作成を維持する。"""
    base = tmp_path / "new"
    path = base / "update-docs" / "SKILL.md"
    assert not path.exists()

    code, out, err = await invoke(NEW, base)

    assert code == 0, (out, err)
    assert path.is_file()
    markdown = path.read_text(encoding="utf-8")
    assert "name: update-docs" in markdown
    assert "## Guides" in markdown
    assert "## API" in markdown
    assert "[A](https://example.com/a)" in markdown
    assert "[C](https://example.com/c)" in markdown
    assert "[API Ref](https://example.com/api)" in markdown
    assert "https://example.com/b" not in markdown
    assert "https://example.com/old" not in markdown
    assert diff_lines(out) == []
