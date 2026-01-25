"""Tests for enricher module."""

from unittest.mock import AsyncMock, patch

import pytest

from llmstxt2skill.enricher import (
    _build_enrichment_prompt,
    _parse_enriched_response,
    enrich_skill,
)
from llmstxt2skill.models import EnrichedSkill, LlmsTxt, LlmsTxtLink, LlmsTxtSection


@pytest.fixture
def sample_llmstxt() -> LlmsTxt:
    """Create a sample LlmsTxt for testing."""
    return LlmsTxt(
        title="Test Documentation",
        description="A test documentation site.",
        sections=[
            LlmsTxtSection(
                title="Getting Started",
                links=[
                    LlmsTxtLink(
                        title="Quick Start",
                        url="https://example.com/quickstart",
                        description="Get started quickly",
                    ),
                    LlmsTxtLink(
                        title="Installation",
                        url="https://example.com/install",
                        description="How to install",
                    ),
                ],
            ),
            LlmsTxtSection(
                title="API Reference",
                links=[
                    LlmsTxtLink(
                        title="REST API",
                        url="https://example.com/api",
                        description="API documentation",
                    ),
                ],
            ),
        ],
    )


class TestBuildEnrichmentPrompt:
    """Tests for _build_enrichment_prompt."""

    def test_includes_title(self, sample_llmstxt: LlmsTxt) -> None:
        """Prompt should include the document title."""
        prompt = _build_enrichment_prompt(sample_llmstxt, lang="ja")
        assert "Test Documentation" in prompt

    def test_includes_sections(self, sample_llmstxt: LlmsTxt) -> None:
        """Prompt should include section information."""
        prompt = _build_enrichment_prompt(sample_llmstxt, lang="ja")
        assert "Getting Started" in prompt
        assert "API Reference" in prompt

    def test_includes_links(self, sample_llmstxt: LlmsTxt) -> None:
        """Prompt should include link information."""
        prompt = _build_enrichment_prompt(sample_llmstxt, lang="ja")
        assert "Quick Start" in prompt
        assert "https://example.com/quickstart" in prompt

    def test_specifies_language(self, sample_llmstxt: LlmsTxt) -> None:
        """Prompt should specify the target language."""
        prompt = _build_enrichment_prompt(sample_llmstxt, lang="ja")
        assert "日本語" in prompt or "Japanese" in prompt

    def test_requests_trigger_conditions(self, sample_llmstxt: LlmsTxt) -> None:
        """Prompt should request trigger conditions."""
        prompt = _build_enrichment_prompt(sample_llmstxt, lang="ja")
        assert "トリガー" in prompt or "trigger" in prompt.lower()


class TestParseEnrichedResponse:
    """Tests for _parse_enriched_response."""

    def test_parses_valid_markdown(self) -> None:
        """Should parse valid markdown response."""
        response = """---
name: test-docs
description: テストドキュメントガイド
---

# テストドキュメントガイド

テスト用のドキュメントです。

## トリガー条件

- 「テストについて教えて」

## このスキルでできること

- ドキュメントの案内

## 概要

| ドキュメント | 説明 |
|-------------|------|
| [クイックスタート](https://example.com/quickstart) | すぐに始める |
"""
        result = _parse_enriched_response(response, "test-docs")
        assert isinstance(result, EnrichedSkill)
        assert result.name == "test-docs"
        # Description is extracted from first paragraph after H1
        assert "テスト用のドキュメント" in result.description
        assert "トリガー条件" in result.content

    def test_handles_response_without_frontmatter(self) -> None:
        """Should handle response without YAML frontmatter."""
        response = """# テストドキュメント

これはテストです。
"""
        result = _parse_enriched_response(response, "test-docs")
        assert result.name == "test-docs"
        assert "テストドキュメント" in result.content


class TestEnrichSkill:
    """Tests for enrich_skill function."""

    @pytest.mark.asyncio
    async def test_calls_provider(self, sample_llmstxt: LlmsTxt) -> None:
        """Should call the LLM provider."""
        mock_response = """# テストドキュメントガイド

テスト用ドキュメントへのナビゲーションスキルです。

## トリガー条件

- 「テストについて教えて」
"""
        mock_provider = AsyncMock()
        mock_provider.generate.return_value = mock_response

        result = await enrich_skill(
            sample_llmstxt,
            name="test-documentation",
            lang="ja",
            provider=mock_provider,
            model="test-model",
        )

        assert mock_provider.generate.called
        assert isinstance(result, EnrichedSkill)
        assert result.name == "test-documentation"

    @pytest.mark.asyncio
    async def test_creates_provider_from_name(self, sample_llmstxt: LlmsTxt) -> None:
        """Should create provider from provider_name."""
        mock_response = "# Test\n\nContent"

        with patch("llmstxt2skill.enricher.create_provider") as mock_create:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = mock_response
            mock_create.return_value = mock_provider

            result = await enrich_skill(
                sample_llmstxt,
                name="test-docs",
                lang="ja",
                provider_name="databricks",
            )

            mock_create.assert_called_once_with("databricks")
            assert isinstance(result, EnrichedSkill)

    @pytest.mark.asyncio
    async def test_uses_default_model(self, sample_llmstxt: LlmsTxt) -> None:
        """Should use default model when not specified."""
        mock_response = "# Test\n\nContent"

        with patch("llmstxt2skill.enricher.create_provider") as mock_create:
            with patch("llmstxt2skill.enricher.get_default_model") as mock_default:
                mock_provider = AsyncMock()
                mock_provider.generate.return_value = mock_response
                mock_create.return_value = mock_provider
                mock_default.return_value = "default-model"

                await enrich_skill(
                    sample_llmstxt,
                    name="test-docs",
                    lang="ja",
                    provider_name="openai",
                )

                mock_default.assert_called_once_with("openai")
                # Check that the request used the default model
                call_args = mock_provider.generate.call_args
                assert call_args[0][0].model == "default-model"
