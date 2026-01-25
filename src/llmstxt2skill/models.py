"""Data models for llmstxt2skill."""

from dataclasses import dataclass, field


@dataclass
class LlmsTxtLink:
    """A link entry in llms.txt."""

    title: str
    url: str
    description: str | None = None


@dataclass
class LlmsTxtSection:
    """A section in llms.txt (H2 heading with links)."""

    title: str
    links: list[LlmsTxtLink] = field(default_factory=list)


@dataclass
class LlmsTxt:
    """Parsed llms.txt content."""

    title: str
    sections: list[LlmsTxtSection] = field(default_factory=list)
    description: str | None = None


@dataclass
class Skill:
    """Claude Code Skill representation."""

    name: str
    description: str
    content: str

    def to_markdown(self) -> str:
        """Generate SKILL.md content with YAML frontmatter."""
        lines = [
            "---",
            f"name: {self.name}",
            f"description: {self.description}",
            "---",
            "",
            self.content,
        ]
        return "\n".join(lines)


@dataclass
class EnrichedSkill:
    """LLM-enriched Claude Code Skill with curated content."""

    name: str
    description: str
    content: str

    def to_markdown(self) -> str:
        """Generate SKILL.md content with YAML frontmatter."""
        lines = [
            "---",
            f"name: {self.name}",
            f"description: {self.description}",
            "---",
            "",
            self.content,
        ]
        return "\n".join(lines)
