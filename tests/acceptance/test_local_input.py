"""ローカル入力と既存 URL 入力の CLI 受け入れテスト。"""

import sys
from unittest.mock import AsyncMock

import httpx
import pytest

from llmstxt2skill.cli import main
from llmstxt2skill.models import EnrichedSkill

LINK = "https://example.com/local-guide"
DOCUMENT = (
    "# Local Docs\n\n"
    "> Local documentation preview.\n\n"
    "## Guides\n"
    f"- [Local Guide]({LINK}): Start here\n"
)


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def http_boundary(monkeypatch):
    """HTTPX の公開送信 API で記録・応答し、実ネットワークを禁止する。"""
    requests = []
    responses = {}

    def respond(request):
        requests.append(request)
        response = responses.get(str(request.url))
        if response is None:
            raise httpx.ConnectError("Network disabled by acceptance test", request=request)
        status, text = response
        return httpx.Response(status, text=text, request=request)

    async def async_send(client, request, *args, **kwargs):
        return respond(request)

    def sync_send(client, request, *args, **kwargs):
        return respond(request)

    monkeypatch.setattr(httpx.AsyncClient, "send", async_send)
    monkeypatch.setattr(httpx.Client, "send", sync_send)
    return requests, responses


@pytest.fixture
def local_file(tmp_path):
    path = tmp_path / "llms.txt"
    path.write_text(DOCUMENT, encoding="utf-8")
    return path


def snapshot(root):
    """dry-run がディレクトリもファイルも作成・変更しないことを確認する。"""
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


async def invoke_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["llmstxt2skill", *map(str, args)])
    try:
        await main()
    except SystemExit as exc:
        code = exc.code
    else:
        code = 0
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.mark.asyncio
@pytest.mark.parametrize("relative", [True, False], ids=["relative", "absolute"])
async def test_ac1_local_dry_run(
    relative, local_file, tmp_path, monkeypatch, capsys, http_boundary
):
    """AC-1: 相対・絶対パスから、HTTP と書き込みなしでプレビューする。"""
    source = "./llms.txt" if relative else str(local_file)
    before = snapshot(tmp_path)

    code, out, err = await invoke_cli(monkeypatch, capsys, source, "--dry-run")

    assert code == 0, err
    assert f"Reading {source}..." in out
    assert "--- SKILL.md (dry-run) ---" in out
    markdown = out.split("--- SKILL.md (dry-run) ---", 1)[1]
    assert "name: local-docs" in markdown
    assert LINK in markdown
    assert err == ""
    assert http_boundary[0] == []
    assert snapshot(tmp_path) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("output_option", ["-o", "--output"])
async def test_ac2_write_refuse_and_force_overwrite(
    output_option, local_file, tmp_path, monkeypatch, capsys, http_boundary
):
    """AC-2: 名前指定で出力し、既存ファイルを保護し、force なら更新する。"""
    output = tmp_path / "output"
    output.mkdir()
    args = [str(local_file), "--name", "my-local", output_option, str(output)]
    target = output / "my-local" / "SKILL.md"

    code, out, err = await invoke_cli(monkeypatch, capsys, *args)
    assert code == 0, err
    assert target.is_file()
    first = target.read_bytes()
    assert "name: my-local" in first.decode("utf-8")
    assert LINK in first.decode("utf-8")

    updated_link = "https://example.com/updated-guide"
    local_file.write_text(DOCUMENT.replace(LINK, updated_link), encoding="utf-8")

    code, out, err = await invoke_cli(monkeypatch, capsys, *args)
    assert code == 1
    assert "Use --force to overwrite" in err
    assert target.read_bytes() == first

    code, out, err = await invoke_cli(monkeypatch, capsys, *args, "--force")
    assert code == 0, err
    updated = target.read_text(encoding="utf-8")
    assert "name: my-local" in updated
    assert updated_link in updated
    assert LINK not in updated
    assert http_boundary[0] == []


@pytest.mark.asyncio
async def test_ac3_local_enrichment_options(
    local_file, tmp_path, monkeypatch, capsys, http_boundary
):
    """AC-3: パース済み入力と指定オプションを偽の enrichment に渡す。"""
    enriched = EnrichedSkill(
        name="local-docs",
        description="Enriched local documentation.",
        content=f"# Enriched local guide\n\n[Guide]({LINK})\n",
    )
    fake_enrich = AsyncMock(return_value=enriched)
    monkeypatch.setattr("llmstxt2skill.enricher.enrich_skill", fake_enrich)
    before = snapshot(tmp_path)

    code, out, err = await invoke_cli(
        monkeypatch,
        capsys,
        local_file,
        "--enrich",
        "--provider", "openai",
        "--lang", "en",
        "--model", "m1",
        "--max-tokens", "1234",
        "--dry-run",
    )

    assert code == 0, err
    fake_enrich.assert_awaited_once()
    call = fake_enrich.await_args
    parsed = call.args[0] if call.args else call.kwargs["llmstxt"]
    assert parsed.title == "Local Docs"
    assert parsed.description == "Local documentation preview."
    assert len(parsed.sections) == 1
    assert parsed.sections[0].title == "Guides"
    assert [link.url for link in parsed.sections[0].links] == [LINK]
    assert call.kwargs["name"] == "local-docs"
    assert call.kwargs["provider_name"] == "openai"
    assert call.kwargs["lang"] == "en"
    assert call.kwargs["model"] == "m1"
    assert call.kwargs["max_tokens"] == 1234
    assert "--- SKILL.md (dry-run) ---" in out
    assert enriched.to_markdown() in out
    assert err == ""
    assert http_boundary[0] == []
    assert snapshot(tmp_path) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["missing", "directory"])
async def test_ac4_unreadable_path_error(
    kind, tmp_path, monkeypatch, capsys, http_boundary
):
    """AC-4: 存在しないパスとディレクトリは、HTTP を使わず明示的に失敗する。"""
    if kind == "missing":
        source = "./no-such-llms.txt"
    else:
        (tmp_path / "docs-directory").mkdir()
        source = "./docs-directory"
    before = snapshot(tmp_path)

    code, out, err = await invoke_cli(monkeypatch, capsys, source, "--dry-run")

    assert code == 1
    assert f"Error: Cannot read {source}:" in err
    assert "Traceback" not in err + out
    assert "--- SKILL.md (dry-run) ---" not in out
    assert http_boundary[0] == []
    assert snapshot(tmp_path) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("scheme", ["http", "https"])
async def test_ac5_url_success_is_preserved(
    scheme, tmp_path, monkeypatch, capsys, http_boundary
):
    """AC-5: URL は HTTP で取得し、応答本文からスキルを生成する。"""
    url = f"{scheme}://example.com/llms.txt"
    requests, responses = http_boundary
    responses[url] = (200, DOCUMENT.replace("Local Docs", "Remote Docs"))
    before = snapshot(tmp_path)

    code, out, err = await invoke_cli(monkeypatch, capsys, url, "--dry-run")

    assert code == 0, err
    assert [(request.method, str(request.url)) for request in requests] == [("GET", url)]
    assert f"Fetching {url}..." in out
    assert "--- SKILL.md (dry-run) ---" in out
    markdown = out.split("--- SKILL.md (dry-run) ---", 1)[1]
    assert "name: remote-docs" in markdown
    assert LINK in markdown
    assert err == ""
    assert snapshot(tmp_path) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("scheme", ["http", "https"])
async def test_ac5_url_404_is_preserved(
    scheme, tmp_path, monkeypatch, capsys, http_boundary
):
    """AC-5: HTTP 404 は Fetch error と終了コード 1 になる。"""
    url = f"{scheme}://example.com/llms.txt"
    requests, responses = http_boundary
    responses[url] = (404, "Not found")
    before = snapshot(tmp_path)

    code, out, err = await invoke_cli(monkeypatch, capsys, url, "--dry-run")

    assert code == 1
    assert [(request.method, str(request.url)) for request in requests] == [("GET", url)]
    assert f"Fetching {url}..." in out
    assert "Fetch error:" in err
    assert "--- SKILL.md (dry-run) ---" not in out
    assert "Traceback" not in err + out
    assert snapshot(tmp_path) == before


@pytest.mark.asyncio
async def test_ac6_help_describes_local_source(monkeypatch, capsys, http_boundary):
    """AC-6: 位置引数の説明に URL と local が記載される。"""
    code, out, err = await invoke_cli(monkeypatch, capsys, "--help")

    assert code == 0
    assert "positional arguments:" in out
    positional_help = out.split("positional arguments:", 1)[1].split("\n\n", 1)[0]
    assert "source" in positional_help
    assert "URL" in positional_help
    assert "local" in positional_help.lower()
    assert err == ""
    assert http_boundary[0] == []
