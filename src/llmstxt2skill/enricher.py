"""LLM-based enricher for Claude Code Skill generation."""

import re

from llmstxt2skill.llm.base import LLMProvider, LLMRequest
from llmstxt2skill.llm.factory import create_provider, get_default_model
from llmstxt2skill.models import EnrichedSkill, LlmsTxt


async def enrich_skill(
    llmstxt: LlmsTxt,
    name: str,
    lang: str = "ja",
    provider: LLMProvider | None = None,
    provider_name: str = "databricks",
    model: str | None = None,
) -> EnrichedSkill:
    """Enrich llms.txt content using LLM to generate high-quality SKILL.md.

    Args:
        llmstxt: Parsed llms.txt content
        name: Skill name (kebab-case)
        lang: Target language (default: ja for Japanese)
        provider: LLM provider instance (if None, created from provider_name)
        provider_name: Name of provider to create (databricks, openai, anthropic, openai-compatible)
        model: Model identifier (defaults to provider's default model)

    Returns:
        EnrichedSkill with curated, translated content
    """
    if provider is None:
        provider = create_provider(provider_name)

    if model is None:
        model = get_default_model(provider_name)

    prompt = _build_enrichment_prompt(llmstxt, lang)
    request = LLMRequest(prompt=prompt, model=model)
    response = await provider.generate(request)
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
元のドキュメントインデックスを翻訳・構造化し、メタ情報を追加します。
{lang_instruction}

# Input Data
以下はllms.txt形式のドキュメントインデックスです：

{input_data}

# CRITICAL RULE - 最重要ルール
**入力データに含まれるリンクは一切削除してはいけません。すべてのリンクを出力に含めてください。**
リンクの削除・省略・要約は禁止です。情報量を減らさないでください。

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

---

### 7. ドキュメントセクション（複数）
各カテゴリごとにH2見出しを付け、テーブル形式でリンクを整理：

| ドキュメント | 説明 |
|-------------|------|
| [日本語タイトル](URL) | 簡潔な日本語説明 |

# Validation Rules
1. **すべてのリンクを必ず出力に含めること（削除禁止）**
2. 元のURLは変更せず、そのまま使用すること
3. タイトルと説明は日本語に翻訳すること
4. 類似したリンクはまとめてカテゴリを再構成しても良い
5. サブセクション（H3）を使って階層化しても良い
6. 各リンクは必ずいずれかのセクションに所属させること

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
