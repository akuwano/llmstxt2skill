"""Tests for llms.txt parser."""

import pytest

from llmstxt2skill.parser import parse_llmstxt


class TestParseTitle:
    def test_extract_h1_title(self):
        content = "# Databricks Documentation\n\nSome content"
        result = parse_llmstxt(content)
        assert result.title == "Databricks Documentation"

    def test_title_with_extra_whitespace(self):
        content = "#   Spaced Title   \n\nContent"
        result = parse_llmstxt(content)
        assert result.title == "Spaced Title"

    def test_no_title_raises_error(self):
        content = "No H1 heading here\n\nJust content"
        with pytest.raises(ValueError, match="No H1 title found"):
            parse_llmstxt(content)


class TestParseDescription:
    def test_extract_blockquote_description(self):
        content = """# Title

> This is the description of the documentation.

## Section
"""
        result = parse_llmstxt(content)
        assert result.description == "This is the description of the documentation."

    def test_multiline_blockquote(self):
        content = """# Title

> First line of description.
> Second line continues.

## Section
"""
        result = parse_llmstxt(content)
        assert result.description == "First line of description. Second line continues."

    def test_no_description(self):
        content = """# Title

## Section
- [Link](https://example.com)
"""
        result = parse_llmstxt(content)
        assert result.description is None


class TestParseSections:
    def test_extract_section(self):
        content = """# Title

## Getting Started

Some section content
"""
        result = parse_llmstxt(content)
        assert len(result.sections) == 1
        assert result.sections[0].title == "Getting Started"

    def test_multiple_sections(self):
        content = """# Title

## Section One

Content

## Section Two

More content
"""
        result = parse_llmstxt(content)
        assert len(result.sections) == 2
        assert result.sections[0].title == "Section One"
        assert result.sections[1].title == "Section Two"


class TestParseLinks:
    def test_extract_link_with_description(self):
        content = """# Title

## Resources
- [Main docs](https://example.com/) - How-to guides and tutorials
"""
        result = parse_llmstxt(content)
        links = result.sections[0].links
        assert len(links) == 1
        assert links[0].title == "Main docs"
        assert links[0].url == "https://example.com/"
        assert links[0].description == "How-to guides and tutorials"

    def test_extract_link_without_description(self):
        content = """# Title

## Resources
- [Quick start](https://example.com/start)
"""
        result = parse_llmstxt(content)
        links = result.sections[0].links
        assert len(links) == 1
        assert links[0].title == "Quick start"
        assert links[0].url == "https://example.com/start"
        assert links[0].description is None

    def test_multiple_links(self):
        content = """# Title

## Resources
- [Doc1](https://example.com/1) - First doc
- [Doc2](https://example.com/2) - Second doc
- [Doc3](https://example.com/3)
"""
        result = parse_llmstxt(content)
        links = result.sections[0].links
        assert len(links) == 3


class TestFullParse:
    def test_databricks_example(self):
        content = """# Databricks Documentation

> Comprehensive documentation for the Databricks platform.

## Overview and getting started
- [Main documentation index](https://docs.databricks.com/) - How-to guides and tutorials
- [Getting started guide](https://docs.databricks.com/getting-started/) - Quick start tutorial

## Data engineering
- [Delta Lake guide](https://docs.databricks.com/delta/) - Table format documentation
"""
        result = parse_llmstxt(content)

        assert result.title == "Databricks Documentation"
        assert result.description == "Comprehensive documentation for the Databricks platform."
        assert len(result.sections) == 2

        section1 = result.sections[0]
        assert section1.title == "Overview and getting started"
        assert len(section1.links) == 2
        assert section1.links[0].title == "Main documentation index"
        assert section1.links[0].url == "https://docs.databricks.com/"
        assert section1.links[0].description == "How-to guides and tutorials"

        section2 = result.sections[1]
        assert section2.title == "Data engineering"
        assert len(section2.links) == 1
