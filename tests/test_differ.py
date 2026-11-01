"""Tests for skill differ."""

from llmstxt2skill.differ import SkillDiff, diff_skills, extract_outline, format_diff
from llmstxt2skill.models import LlmsTxtLink

OLD = """---
name: test-docs
description: Test [not a link](https://example.com/frontmatter)
---

# Test Docs

## Guides
- [A](https://example.com/a)
- [B](https://example.com/b) - Second

## Legacy
- [Old](https://example.com/old)
"""

NEW = """---
name: test-docs
description: Test
---

# Test Docs

## Guides
- [Renamed A](https://example.com/a)
- [C](https://example.com/c)

## API
- [API Ref](https://example.com/api)
"""


class TestExtractOutline:
    def test_sections_and_links(self):
        sections, links = extract_outline(OLD)
        assert sections == ["Guides", "Legacy"]
        assert [link.url for link in links] == [
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/old",
        ]
        assert links[1].title == "B"

    def test_skips_frontmatter(self):
        _, links = extract_outline(OLD)
        assert "https://example.com/frontmatter" not in [link.url for link in links]

    def test_skips_code_blocks(self):
        markdown = "## Real\n```\n## Not a section\n[x](https://example.com/x)\n```\n"
        sections, links = extract_outline(markdown)
        assert sections == ["Real"]
        assert links == []

    def test_skips_tilde_code_blocks(self):
        markdown = "~~~markdown\n## Example\n[x](https://example.com/x)\n~~~\n[y](https://example.com/y)\n"
        sections, links = extract_outline(markdown)
        assert sections == []
        assert [link.url for link in links] == ["https://example.com/y"]

    def test_longer_fence_is_not_closed_by_shorter_fence(self):
        markdown = (
            "````markdown\n"
            "```\n"
            "## Example\n"
            "[x](https://example.com/x)\n"
            "```\n"
            "[z](https://example.com/z)\n"
            "````\n"
            "## Real\n"
            "[y](https://example.com/y)\n"
        )
        sections, links = extract_outline(markdown)
        assert sections == ["Real"]
        assert [link.url for link in links] == ["https://example.com/y"]

    def test_backtick_fence_is_not_closed_by_tilde_fence(self):
        markdown = "```\n~~~\n[x](https://example.com/x)\n```\n[y](https://example.com/y)\n"
        _, links = extract_outline(markdown)
        assert [link.url for link in links] == ["https://example.com/y"]

    def test_deduplicates_by_url_keeping_first_title(self):
        markdown = "- [First](https://example.com/a)\n- [Second](https://example.com/a)\n"
        _, links = extract_outline(markdown)
        assert links == [LlmsTxtLink(title="First", url="https://example.com/a")]

    def test_links_in_tables(self):
        markdown = "| [A](https://example.com/a) | [B](https://example.com/b) |\n"
        _, links = extract_outline(markdown)
        assert [link.url for link in links] == ["https://example.com/a", "https://example.com/b"]


class TestDiffSkills:
    def test_added_and_removed(self):
        diff = diff_skills(OLD, NEW)
        assert diff.added_sections == ["API"]
        assert diff.removed_sections == ["Legacy"]
        assert [link.url for link in diff.added_links] == [
            "https://example.com/c",
            "https://example.com/api",
        ]
        assert [link.title for link in diff.removed_links] == ["B", "Old"]
        assert diff.has_changes

    def test_no_changes(self):
        diff = diff_skills(OLD, OLD)
        assert diff == SkillDiff([], [], [], [])
        assert not diff.has_changes


class TestFormatDiff:
    def test_format_changes(self):
        output = format_diff(diff_skills(OLD, NEW))
        assert output.splitlines() == [
            "Changes:",
            "  Sections added (1):",
            "    + API",
            "  Sections removed (1):",
            "    - Legacy",
            "  Links added (2):",
            "    + [C](https://example.com/c)",
            "    + [API Ref](https://example.com/api)",
            "  Links removed (2):",
            "    - [B](https://example.com/b)",
            "    - [Old](https://example.com/old)",
        ]

    def test_format_omits_empty_groups(self):
        old = "- [A](https://example.com/a)\n"
        new = "- [A](https://example.com/a)\n- [B](https://example.com/b)\n"
        output = format_diff(diff_skills(old, new))
        assert output.splitlines() == [
            "Changes:",
            "  Links added (1):",
            "    + [B](https://example.com/b)",
        ]

    def test_format_no_changes(self):
        assert format_diff(diff_skills(OLD, OLD)) == "No changes in sections or links."
