"""File writer for Claude Code Skills."""

from pathlib import Path

from llmstxt2skill.models import Skill


def get_skill_path(name: str, base_path: Path | None = None) -> Path:
    """Get the path where a skill should be written.

    Args:
        name: Skill name (used as directory name)
        base_path: Base directory for skills (defaults to ~/.claude/skills)

    Returns:
        Full path to SKILL.md file
    """
    if base_path is None:
        base_path = Path.home() / ".claude" / "skills"
    return base_path / name / "SKILL.md"


def write_skill(
    skill: Skill,
    base_path: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> Path | None:
    """Write a skill to disk.

    Args:
        skill: Skill to write
        base_path: Base directory for skills (defaults to ~/.claude/skills)
        force: Overwrite existing file if True
        dry_run: Don't write, just return None

    Returns:
        Path to written file, or None if dry_run

    Raises:
        FileExistsError: If file exists and force is False
    """
    if dry_run:
        return None

    path = get_skill_path(skill.name, base_path)

    if path.exists() and not force:
        raise FileExistsError(f"Skill already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(skill.to_markdown())

    return path
