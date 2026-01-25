"""Tests for data models."""

from llmstxt2skill.models import LlmsTxt, LlmsTxtLink, LlmsTxtSection, Skill


class TestLlmsTxtLink:
    def test_create_link(self):
        link = LlmsTxtLink(
            title="Main documentation",
            url="https://docs.example.com/",
            description="How-to guides and tutorials",
        )
        assert link.title == "Main documentation"
        assert link.url == "https://docs.example.com/"
        assert link.description == "How-to guides and tutorials"

    def test_link_without_description(self):
        link = LlmsTxtLink(
            title="Quick start",
            url="https://docs.example.com/quickstart",
        )
        assert link.title == "Quick start"
        assert link.description is None


class TestLlmsTxtSection:
    def test_create_section(self):
        links = [
            LlmsTxtLink(title="Doc1", url="https://example.com/1"),
            LlmsTxtLink(title="Doc2", url="https://example.com/2"),
        ]
        section = LlmsTxtSection(title="Getting Started", links=links)
        assert section.title == "Getting Started"
        assert len(section.links) == 2

    def test_section_with_empty_links(self):
        section = LlmsTxtSection(title="Empty Section", links=[])
        assert section.title == "Empty Section"
        assert section.links == []


class TestLlmsTxt:
    def test_create_llmstxt(self):
        sections = [
            LlmsTxtSection(title="Overview", links=[]),
        ]
        llmstxt = LlmsTxt(
            title="Databricks Documentation",
            description="Comprehensive documentation for the Databricks platform",
            sections=sections,
        )
        assert llmstxt.title == "Databricks Documentation"
        assert llmstxt.description == "Comprehensive documentation for the Databricks platform"
        assert len(llmstxt.sections) == 1

    def test_llmstxt_without_description(self):
        llmstxt = LlmsTxt(
            title="Simple Docs",
            sections=[],
        )
        assert llmstxt.description is None


class TestSkill:
    def test_create_skill(self):
        skill = Skill(
            name="databricks-documentation",
            description="Comprehensive documentation for the Databricks platform",
            content="# Databricks Documentation\n\nSome content here.",
        )
        assert skill.name == "databricks-documentation"
        assert skill.description == "Comprehensive documentation for the Databricks platform"
        assert "# Databricks Documentation" in skill.content

    def test_skill_to_markdown(self):
        skill = Skill(
            name="my-skill",
            description="A test skill",
            content="# My Skill\n\nContent here.",
        )
        md = skill.to_markdown()
        assert "---" in md
        assert "name: my-skill" in md
        assert "description: A test skill" in md
        assert "# My Skill" in md
