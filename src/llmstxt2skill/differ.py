"""Differ for comparing two SKILL.md files."""

import re
from dataclasses import dataclass

from llmstxt2skill.models import LlmsTxtLink

# Markdown link: [title](url), excluding images ![alt](src).
# The URL may contain one level of balanced parentheses (e.g. .../Spark_(software)).
LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)")

# Fenced code block delimiter: ``` or ~~~ (3 or more), up to 3 spaces of indent
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


@dataclass
class SkillDiff:
    """Sections and links added or removed between two skills."""

    added_sections: list[str]
    removed_sections: list[str]
    added_links: list[LlmsTxtLink]
    removed_links: list[LlmsTxtLink]

    @property
    def has_changes(self) -> bool:
        """Return True if any section or link was added or removed."""
        return bool(
            self.added_sections
            or self.removed_sections
            or self.added_links
            or self.removed_links
        )


def extract_outline(markdown: str) -> tuple[list[str], list[LlmsTxtLink]]:
    """Extract H2 sections and links from SKILL.md content.

    YAML frontmatter and fenced code blocks are skipped. Links are
    deduplicated by URL, keeping the first title.

    Args:
        markdown: SKILL.md content

    Returns:
        Tuple of (section titles, links) in order of appearance
    """
    lines = markdown.splitlines()

    # Skip YAML frontmatter
    start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start = i + 1
                break

    sections: list[str] = []
    links: list[LlmsTxtLink] = []
    seen_urls: set[str] = set()
    # Opening fence of the current code block (None when outside)
    open_fence: str | None = None

    for line in lines[start:]:
        fence = FENCE_PATTERN.match(line)
        if open_fence is None:
            if fence:
                open_fence = fence.group(1)
                continue
        else:
            # Closed only by the same character, at least as long, with nothing after
            if (
                fence
                and fence.group(1)[0] == open_fence[0]
                and len(fence.group(1)) >= len(open_fence)
                and not fence.group(2).strip()
            ):
                open_fence = None
            continue

        if line.startswith("## "):
            title = line[3:].strip()
            if title not in sections:
                sections.append(title)

        for match in LINK_PATTERN.finditer(line):
            title, url = match.group(1), match.group(2)
            if url not in seen_urls:
                seen_urls.add(url)
                links.append(LlmsTxtLink(title=title, url=url))

    return sections, links


def diff_skills(old_markdown: str, new_markdown: str) -> SkillDiff:
    """Compare two SKILL.md contents by H2 sections and link URLs.

    Args:
        old_markdown: Existing SKILL.md content
        new_markdown: Regenerated SKILL.md content

    Returns:
        SkillDiff (added in new order, removed in old order)
    """
    old_sections, old_links = extract_outline(old_markdown)
    new_sections, new_links = extract_outline(new_markdown)

    old_urls = {link.url for link in old_links}
    new_urls = {link.url for link in new_links}

    return SkillDiff(
        added_sections=[s for s in new_sections if s not in old_sections],
        removed_sections=[s for s in old_sections if s not in new_sections],
        added_links=[link for link in new_links if link.url not in old_urls],
        removed_links=[link for link in old_links if link.url not in new_urls],
    )


def format_diff(diff: SkillDiff) -> str:
    """Format a SkillDiff for terminal output.

    Args:
        diff: Diff to format

    Returns:
        Human-readable summary of changes
    """
    if not diff.has_changes:
        return "No changes in sections or links."

    lines = ["Changes:"]
    groups = [
        ("Sections added", "+", diff.added_sections),
        ("Sections removed", "-", diff.removed_sections),
        ("Links added", "+", [f"[{lk.title}]({lk.url})" for lk in diff.added_links]),
        ("Links removed", "-", [f"[{lk.title}]({lk.url})" for lk in diff.removed_links]),
    ]
    for label, mark, items in groups:
        if not items:
            continue
        lines.append(f"  {label} ({len(items)}):")
        lines.extend(f"    {mark} {item}" for item in items)

    return "\n".join(lines)
