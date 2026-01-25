# llmstxt2skill

Convert [llms.txt](https://llmstxt.org/) files to [Claude Code](https://docs.anthropic.com/en/docs/claude-code) Skill format.

## Installation

```bash
uv pip install -e .
```

## Usage

```bash
# Basic usage
llmstxt2skill https://docs.databricks.com/llms.txt

# Preview without writing (dry-run)
llmstxt2skill https://docs.databricks.com/llms.txt --dry-run

# Custom skill name
llmstxt2skill https://docs.databricks.com/llms.txt --name databricks

# Overwrite existing skill
llmstxt2skill https://docs.databricks.com/llms.txt --force
```

## Output

Skills are written to `~/.claude/skills/{skill-name}/SKILL.md`

### Example

**Input** (`llms.txt`):
```markdown
# Databricks Documentation

> Comprehensive documentation for the Databricks platform.

## Overview
- [Main docs](https://docs.databricks.com/) - How-to guides
```

**Output** (`SKILL.md`):
```yaml
---
name: databricks-documentation
description: Comprehensive documentation for the Databricks platform.
---

# Databricks Documentation

Comprehensive documentation for the Databricks platform.

## Overview
- [Main docs](https://docs.databricks.com/) - How-to guides
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check src/ tests/
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
