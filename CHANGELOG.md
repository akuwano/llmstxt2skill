# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--update` option to regenerate an existing skill and show added/removed sections and links

## [0.2.4] - 2025-01-25

### Fixed
- Support colon (`:`) separator for link descriptions per llms.txt spec
- Parse links under H1 when no H2 sections exist (e.g., LangGraph llms.txt)

## [0.2.3] - 2025-01-25

### Changed
- Updated README with latest options and examples

## [0.2.2] - 2025-01-25

### Added
- `--max-tokens` option to control LLM output token limit (default: 16000)

### Changed
- Increased default max_tokens from 4000 to 16000 for large llms.txt files

## [0.2.1] - 2025-01-25

### Added
- `-v`/`--version` flag to display version information

## [0.2.0] - 2025-01-25

### Added
- LLM enrichment with `--enrich` option for high-quality skill generation
- Multi-provider support: Databricks, OpenAI, Anthropic, OpenAI-compatible (local LLMs)
- `--provider` option to select LLM provider
- `--lang` option for target language (default: Japanese)
- `--model` option to specify model identifier

### Changed
- Enrichment now preserves all links (no curation/deletion)
- LLM role changed from curation to translation and structuring only

## [0.1.0] - 2025-01-25

### Added
- Initial release
- CLI tool to convert llms.txt to Claude Code Skill format
- URL fetching with httpx
- llms.txt parsing (H1 title, blockquote description, H2 sections, links)
- Skill markdown generation with YAML frontmatter
- File output to `~/.claude/skills/`
- CLI options: `--dry-run`, `--force`, `--name`, `--output`
