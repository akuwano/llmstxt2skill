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

# Custom output directory
llmstxt2skill https://docs.databricks.com/llms.txt -o ./skills

# Overwrite existing skill
llmstxt2skill https://docs.databricks.com/llms.txt --force
```

## Options

| Option | Description |
|--------|-------------|
| `--name` | Custom skill name (defaults to kebab-case of title) |
| `-o, --output` | Output directory (defaults to `~/.claude/skills`) |
| `--dry-run` | Preview output without writing files |
| `--force` | Overwrite existing skill |

## Output

By default, skills are written to `~/.claude/skills/{skill-name}/SKILL.md`

Use `-o` or `--output` to specify a custom output directory:
```bash
llmstxt2skill https://example.com/llms.txt -o ./my-skills
# Output: ./my-skills/{skill-name}/SKILL.md
```

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
