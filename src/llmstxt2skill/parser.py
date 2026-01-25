"""Parser for llms.txt format."""

import re

from llmstxt2skill.models import LlmsTxt, LlmsTxtLink, LlmsTxtSection


def parse_llmstxt(content: str) -> LlmsTxt:
    """Parse llms.txt content into structured data.

    Args:
        content: Raw llms.txt markdown content

    Returns:
        Parsed LlmsTxt object

    Raises:
        ValueError: If no H1 title is found
    """
    title = _extract_title(content)
    description = _extract_description(content)
    sections = _extract_sections(content)

    return LlmsTxt(title=title, description=description, sections=sections)


def _extract_title(content: str) -> str:
    """Extract H1 title from content."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not match:
        raise ValueError("No H1 title found in llms.txt")
    return match.group(1).strip()


def _extract_description(content: str) -> str | None:
    """Extract blockquote description from content."""
    # Find all consecutive blockquote lines after the title
    lines = content.split("\n")
    blockquote_lines = []
    in_blockquote = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            in_blockquote = True
            # Remove the > prefix and strip
            text = stripped[1:].strip()
            if text:
                blockquote_lines.append(text)
        elif in_blockquote and stripped:
            # End of blockquote block
            break
        elif in_blockquote and not stripped:
            # Empty line might end blockquote
            break

    if not blockquote_lines:
        return None

    return " ".join(blockquote_lines)


def _extract_sections(content: str) -> list[LlmsTxtSection]:
    """Extract H2 sections with their links."""
    sections = []

    # Split by H2 headers
    pattern = r"^##\s+(.+)$"
    parts = re.split(pattern, content, flags=re.MULTILINE)

    # parts[0] is content before first H2, then alternating title/content
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            title = parts[i].strip()
            section_content = parts[i + 1]
            links = _extract_links(section_content)
            sections.append(LlmsTxtSection(title=title, links=links))
        else:
            # Last section might not have content
            title = parts[i].strip()
            sections.append(LlmsTxtSection(title=title, links=[]))

    return sections


def _extract_links(content: str) -> list[LlmsTxtLink]:
    """Extract markdown links from section content."""
    links = []

    # Pattern: - [title](url) - description OR - [title](url)
    pattern = r"^-\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*-\s*(.+))?$"

    for line in content.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            title = match.group(1).strip()
            url = match.group(2).strip()
            description = match.group(3).strip() if match.group(3) else None
            links.append(LlmsTxtLink(title=title, url=url, description=description))

    return links
