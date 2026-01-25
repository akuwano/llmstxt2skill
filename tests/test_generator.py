"""Tests for Skill generator."""

from llmstxt2skill.generator import generate_skill, to_kebab_case
from llmstxt2skill.models import LlmsTxt, LlmsTxtLink, LlmsTxtSection


class TestToKebabCase:
    def test_simple_title(self):
        assert to_kebab_case("Databricks Documentation") == "databricks-documentation"

    def test_single_word(self):
        assert to_kebab_case("Python") == "python"

    def test_multiple_spaces(self):
        assert to_kebab_case("My  Great   Tool") == "my-great-tool"

    def test_special_characters(self):
        assert to_kebab_case("API (v2) Docs") == "api-v2-docs"

    def test_already_kebab(self):
        assert to_kebab_case("already-kebab") == "already-kebab"


class TestGenerateSkill:
    def test_basic_generation(self):
        llmstxt = LlmsTxt(
            title="My Docs",
            description="Documentation for my project.",
            sections=[],
        )
        skill = generate_skill(llmstxt)

        assert skill.name == "my-docs"
        assert skill.description == "Documentation for my project."
        assert "# My Docs" in skill.content

    def test_with_custom_name(self):
        llmstxt = LlmsTxt(
            title="Long Documentation Title",
            description="A description",
            sections=[],
        )
        skill = generate_skill(llmstxt, name="short-name")

        assert skill.name == "short-name"

    def test_content_includes_description(self):
        llmstxt = LlmsTxt(
            title="Title",
            description="The description text.",
            sections=[],
        )
        skill = generate_skill(llmstxt)

        assert "The description text." in skill.content

    def test_content_includes_sections(self):
        llmstxt = LlmsTxt(
            title="Title",
            description="Description",
            sections=[
                LlmsTxtSection(
                    title="Getting Started",
                    links=[
                        LlmsTxtLink(
                            title="Quick Start",
                            url="https://example.com/start",
                            description="Start here",
                        ),
                    ],
                ),
            ],
        )
        skill = generate_skill(llmstxt)

        assert "## Getting Started" in skill.content
        assert "[Quick Start](https://example.com/start)" in skill.content
        assert "Start here" in skill.content

    def test_full_markdown_output(self):
        llmstxt = LlmsTxt(
            title="Databricks Documentation",
            description="Comprehensive docs.",
            sections=[
                LlmsTxtSection(
                    title="Overview",
                    links=[
                        LlmsTxtLink(
                            title="Main docs",
                            url="https://docs.databricks.com/",
                            description="How-to guides",
                        ),
                        LlmsTxtLink(
                            title="API reference",
                            url="https://docs.databricks.com/api",
                        ),
                    ],
                ),
            ],
        )
        skill = generate_skill(llmstxt)
        md = skill.to_markdown()

        assert md.startswith("---\n")
        assert "name: databricks-documentation" in md
        assert "description: Comprehensive docs." in md
        assert "---" in md
        assert "# Databricks Documentation" in md

    def test_no_description_uses_title(self):
        llmstxt = LlmsTxt(
            title="Simple Docs",
            description=None,
            sections=[],
        )
        skill = generate_skill(llmstxt)

        assert skill.description == "Simple Docs"
