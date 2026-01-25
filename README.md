# llmstxt2skill

Convert [llms.txt](https://llmstxt.org/) files to [Claude Code](https://docs.anthropic.com/en/docs/claude-code) Skill format.

## Installation

```bash
pip install llmstxt2skill
```

For development:
```bash
git clone https://github.com/akuwano/llmstxt2skill.git
cd llmstxt2skill
uv pip install -e ".[dev]"
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
| `--enrich` | Use LLM to generate enriched skill with curation and localization |
| `--provider` | LLM provider: `databricks`, `openai`, `anthropic`, `openai-compatible` (default: `databricks`) |
| `--lang` | Target language for enriched skill (default: `ja`) |
| `--model` | Model identifier (defaults to provider's default model) |

## LLM Enrichment

Use `--enrich` to generate high-quality skills with:
- Localized content (Japanese by default)
- Curated and categorized links
- Trigger conditions for when to use the skill
- Capabilities and limitations
- Usage instructions

> **Note:** The `--enrich` option calls external LLM APIs, which may incur costs depending on your provider and usage.

### Supported Providers

| Provider | Environment Variables | Default Model |
|----------|----------------------|---------------|
| `databricks` | `DATABRICKS_HOST`, `DATABRICKS_TOKEN` | `databricks-gemini-3-pro` |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| `openai-compatible` | `OPENAI_BASE_URL`, `OPENAI_API_KEY` (optional) | `default` |

> **Note:** The `openai-compatible` provider is intended for local LLM servers (vLLM, Ollama, llama.cpp) and uses HTTP by default. For production use with remote endpoints, ensure HTTPS is configured.

### Examples

```bash
# Databricks (default provider)
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
llmstxt2skill https://docs.databricks.com/llms.txt --enrich

# OpenAI
export OPENAI_API_KEY="sk-..."
llmstxt2skill https://example.com/llms.txt --enrich --provider openai

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
llmstxt2skill https://example.com/llms.txt --enrich --provider anthropic

# Local LLM (vLLM, Ollama, llama.cpp server)
export OPENAI_BASE_URL="http://localhost:8000"
llmstxt2skill https://example.com/llms.txt --enrich --provider openai-compatible --model llama3

# Specify model explicitly
llmstxt2skill https://example.com/llms.txt --enrich --provider openai --model gpt-4o

# English output
llmstxt2skill https://example.com/llms.txt --enrich --lang en
```

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
