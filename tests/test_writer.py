"""Tests for Skill file writer."""

from pathlib import Path

import pytest

from llmstxt2skill.models import Skill
from llmstxt2skill.writer import get_skill_path, write_skill


class TestGetSkillPath:
    def test_default_path(self):
        path = get_skill_path("my-skill")
        expected = Path.home() / ".claude" / "skills" / "my-skill" / "SKILL.md"
        assert path == expected

    def test_custom_base_path(self, tmp_path):
        path = get_skill_path("my-skill", base_path=tmp_path)
        expected = tmp_path / "my-skill" / "SKILL.md"
        assert path == expected


class TestWriteSkill:
    def test_write_creates_directory(self, tmp_path):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            content="# Test\n\nContent here.",
        )

        path = write_skill(skill, base_path=tmp_path)

        assert path.exists()
        assert path.parent.name == "test-skill"

    def test_write_content(self, tmp_path):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            content="# Test\n\nContent here.",
        )

        path = write_skill(skill, base_path=tmp_path)
        content = path.read_text()

        assert "---" in content
        assert "name: test-skill" in content
        assert "description: A test skill" in content
        assert "# Test" in content

    def test_write_existing_raises_without_force(self, tmp_path):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            content="# Test",
        )

        # Write first time
        write_skill(skill, base_path=tmp_path)

        # Second write should fail
        with pytest.raises(FileExistsError):
            write_skill(skill, base_path=tmp_path)

    def test_write_existing_with_force(self, tmp_path):
        skill = Skill(
            name="test-skill",
            description="First version",
            content="# Test",
        )
        write_skill(skill, base_path=tmp_path)

        skill2 = Skill(
            name="test-skill",
            description="Second version",
            content="# Test Updated",
        )
        path = write_skill(skill2, base_path=tmp_path, force=True)

        content = path.read_text()
        assert "Second version" in content

    def test_dry_run_does_not_write(self, tmp_path):
        skill = Skill(
            name="test-skill",
            description="A test skill",
            content="# Test",
        )

        result = write_skill(skill, base_path=tmp_path, dry_run=True)

        assert result is None
        skill_dir = tmp_path / "test-skill"
        assert not skill_dir.exists()
