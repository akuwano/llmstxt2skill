"""LLM-based enricher for Claude Code Skill generation."""

import os
import re

import httpx

from llmstxt2skill.models import EnrichedSkill, LlmsTxt

# Default Databricks serving endpoint
DEFAULT_MODEL = "databricks-gemini-3-pro"


async def enrich_skill(
    llmstxt: LlmsTxt,
    name: str,
    lang: str = "ja",
    model: str = DEFAULT_MODEL,
) -> EnrichedSkill:
    """Enrich llms.txt content using LLM to generate high-quality SKILL.md.

    Args:
        llmstxt: Parsed llms.txt content
        name: Skill name (kebab-case)
        lang: Target language (default: ja for Japanese)
        model: Databricks serving endpoint model name

    Returns:
        EnrichedSkill with curated, translated content
    """
    prompt = _build_enrichment_prompt(llmstxt, lang)
    response = await _call_llm(prompt, model)
    return _parse_enriched_response(response, name)


def _build_enrichment_prompt(llmstxt: LlmsTxt, lang: str = "ja") -> str:
    """Build the prompt for LLM enrichment.

    Args:
        llmstxt: Parsed llms.txt content
        lang: Target language

    Returns:
        Prompt string for LLM
    """
    # Build input data section from llmstxt
    input_sections = []
    for section in llmstxt.sections:
        links_text = "\n".join(
            f"  - [{link.title}]({link.url}): {link.description or 'N/A'}"
            for link in section.links
        )
        input_sections.append(f"### {section.title}\n{links_text}")

    input_data = f"""# {llmstxt.title}
{llmstxt.description or ''}

{chr(10).join(input_sections)}"""

    # Language-specific instructions
    if lang == "ja":
        lang_instruction = "すべての出力は日本語で記述してください。"
        trigger_examples = """- 「〇〇について教えて」
- 「〇〇の設定方法」
- 「〇〇でエラーが出る」
- 「〇〇の使い方」"""
    else:
        lang_instruction = f"Write all output in {lang}."
        trigger_examples = """- "How do I..."
- "What is..."
- "How to configure..."
- "Error with..."""

    prompt = f"""# Role
あなたはClaude Codeのためのスキル定義ファイル（SKILL.md）を作成する専門家です。
ユーザーの生産性を最大化するため、膨大なドキュメントから「本当に必要な情報」だけを抽出し、構造化します。
{lang_instruction}

# Input Data
以下はllms.txt形式のドキュメントインデックスです：

{input_data}

# Output Requirements
以下の構造を持つMarkdownを出力してください。YAMLフロントマターは不要です（後で自動付与されます）。

## 必須セクション

### 1. タイトル（H1）
ドキュメントの日本語タイトル（例：「Databricks ドキュメントガイド」）

### 2. 概要説明
1-2文でこのスキルが何をするか説明

### 3. トリガー条件
「以下のような質問・依頼があった場合にこのスキルを使用してください：」という見出しで、
具体的な質問例をリスト形式で記載。例：
{trigger_examples}

### 4. このスキルでできること
箇条書きで3-5項目

### 5. このスキルでできないこと
箇条書きで2-3項目（実際のシステム操作、環境固有の設定など）

### 6. 使用手順
1. ユーザーの質問・目的を確認
2. 該当するセクションからドキュメントリンクを特定
3. リンクと概要説明を提供
4. 必要に応じて関連ドキュメントも案内

### 7. ドキュメントセクション（複数）
各カテゴリごとにH2見出しを付け、テーブル形式でリンクを整理：

| ドキュメント | 説明 |
|-------------|------|
| [タイトル](URL) | 簡潔な説明（1行） |

# Validation Rules
1. リンクは重要度が高いものを優先し、各セクション最大10件程度に絞り込むこと
2. 元のURLは変更せず、そのまま使用すること
3. 説明文は簡潔に（20文字以内を目安）
4. 類似したリンクはまとめてカテゴリを再構成しても良い
5. サブセクション（H3）を使って階層化しても良い

# Output
上記の構造に従ったMarkdownを出力してください。"""

    return prompt


def _parse_enriched_response(response: str, name: str) -> EnrichedSkill:
    """Parse LLM response into EnrichedSkill.

    Args:
        response: LLM response text
        name: Skill name to use

    Returns:
        EnrichedSkill object
    """
    content = response.strip()

    # Remove YAML frontmatter if present (we'll add our own)
    frontmatter_pattern = r"^---\s*\n.*?\n---\s*\n"
    content = re.sub(frontmatter_pattern, "", content, flags=re.DOTALL)
    content = content.strip()

    # Extract description from content (first paragraph after H1)
    description = _extract_description(content)

    return EnrichedSkill(
        name=name,
        description=description,
        content=content,
    )


def _extract_description(content: str) -> str:
    """Extract description from markdown content.

    Args:
        content: Markdown content

    Returns:
        Description string
    """
    lines = content.split("\n")
    description_lines = []
    found_title = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            found_title = True
            continue
        if found_title:
            if stripped.startswith("#"):
                # Hit next heading, stop
                break
            if stripped:
                description_lines.append(stripped)
            elif description_lines:
                # Empty line after content, stop
                break

    description = " ".join(description_lines)
    # Truncate if too long
    if len(description) > 200:
        description = description[:197] + "..."
    return description if description else "ドキュメントガイド"


async def _call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call Databricks LLM serving endpoint.

    Args:
        prompt: Prompt text
        model: Model endpoint name

    Returns:
        LLM response text

    Raises:
        ValueError: If DATABRICKS_HOST or DATABRICKS_TOKEN not set
        httpx.HTTPError: If API call fails
    """
    host = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
    token = os.environ.get("DATABRICKS_TOKEN", "")

    if not host or not token:
        raise ValueError(
            "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables must be set"
        )

    endpoint_url = f"{host}/serving-endpoints/{model}/invocations"

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            endpoint_url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
            },
        )
        response.raise_for_status()
        result = response.json()

        # Handle different response formats
        content = result["choices"][0]["message"]["content"]
        if isinstance(content, list):
            # Some models return content as a list of parts
            content = content[0].get("text", str(content[0]))
        return content
