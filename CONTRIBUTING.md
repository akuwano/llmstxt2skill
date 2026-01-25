# Contributing to llmstxt2skill

Thank you for your interest in contributing!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/akuwano/llmstxt2skill.git
   cd llmstxt2skill
   ```

2. Install dependencies with uv:
   ```bash
   uv sync --all-extras
   ```

3. Run tests:
   ```bash
   uv run pytest tests/ -v
   ```

4. Run linter:
   ```bash
   uv run ruff check src/ tests/
   ```

## Development Workflow

This project follows TDD (Test-Driven Development):

1. **Red**: Write a failing test first
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Improve the code while keeping tests green

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

# Examples
feat(cli): add --verbose option
fix(parser): handle empty sections
test(generator): add edge case tests
docs(readme): update installation instructions
```

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| refactor | Code refactoring |
| test | Adding or updating tests |
| docs | Documentation changes |
| chore | Maintenance tasks |

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes with tests
4. Ensure all tests pass and linting is clean
5. Submit a pull request

## Code Style

- Python 3.11+
- Follow existing code patterns
- Use type hints
- Keep functions focused and small
