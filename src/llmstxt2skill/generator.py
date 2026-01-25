"""Generator for Claude Code Skill from LlmsTxt."""

import re

from llmstxt2skill.models import LlmsTxt, Skill


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case.

    Args:
        text: Input text (e.g., "Databricks Documentation")

    Returns:
        Kebab-case string (e.g., "databricks-documentation")
    """
    # Replace non-alphanumeric with spaces
    text = re.sub(r"[^a-zA-Z0-9\s-]", " ", text)
    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    # Convert to lowercase and replace spaces with hyphens
    text = text.strip().lower().replace(" ", "-")
    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)
    return text


def generate_skill(llmstxt: LlmsTxt, name: str | None = None) -> Skill:
    """Generate a Skill from parsed LlmsTxt.

    Args:
        llmstxt: Parsed llms.txt content
        name: Optional custom skill name (defaults to kebab-case of title)

    Returns:
        Generated Skill object
    """
    skill_name = name if name else to_kebab_case(llmstxt.title)
    description = llmstxt.description if llmstxt.description else llmstxt.title
    content = _generate_content(llmstxt)

    return Skill(name=skill_name, description=description, content=content)


def _generate_content(llmstxt: LlmsTxt) -> str:
    """Generate markdown content for the skill."""
    lines = []

    # Title
    lines.append(f"# {llmstxt.title}")
    lines.append("")

    # Description
    if llmstxt.description:
        lines.append(llmstxt.description)
        lines.append("")

    # Sections
    for section in llmstxt.sections:
        lines.append(f"## {section.title}")

        for link in section.links:
            if link.description:
                lines.append(f"- [{link.title}]({link.url}) - {link.description}")
            else:
                lines.append(f"- [{link.title}]({link.url})")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
