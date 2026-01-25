"""CLI entry point for llmstxt2skill."""

import argparse
import asyncio
import sys
from pathlib import Path

from llmstxt2skill.fetcher import fetch_llmstxt
from llmstxt2skill.generator import generate_skill, to_kebab_case
from llmstxt2skill.parser import parse_llmstxt
from llmstxt2skill.writer import write_skill


def get_default_base_path() -> Path:
    """Get the default base path for skills."""
    return Path.home() / ".claude" / "skills"


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Arguments to parse (defaults to sys.argv[1:])

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="llmstxt2skill",
        description="Convert llms.txt to Claude Code Skill format",
    )
    parser.add_argument(
        "url",
        help="URL to llms.txt file (e.g., https://docs.databricks.com/llms.txt)",
    )
    parser.add_argument(
        "--name",
        help="Custom skill name (defaults to kebab-case of title)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory (defaults to ~/.claude/skills)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing skill",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Use LLM to generate enriched skill with curation and localization",
    )
    parser.add_argument(
        "--provider",
        default="databricks",
        choices=["databricks", "openai", "anthropic", "openai-compatible"],
        help="LLM provider for enrichment (default: databricks)",
    )
    parser.add_argument(
        "--lang",
        default="ja",
        help="Target language for enriched skill (default: ja)",
    )
    parser.add_argument(
        "--model",
        help="Model identifier (defaults to provider's default model)",
    )

    return parser.parse_args(args)


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        # Fetch
        print(f"Fetching {args.url}...")
        content = await fetch_llmstxt(args.url)

        # Parse
        llmstxt = parse_llmstxt(content)
        print(f"Parsed: {llmstxt.title}")

        # Generate skill name
        skill_name = args.name if args.name else to_kebab_case(llmstxt.title)

        # Generate (with or without LLM enrichment)
        if args.enrich:
            from llmstxt2skill.enricher import enrich_skill
            from llmstxt2skill.llm.factory import get_default_model

            model = args.model or get_default_model(args.provider)
            print(f"Enriching with {args.provider} ({model})...")
            skill = await enrich_skill(
                llmstxt,
                name=skill_name,
                lang=args.lang,
                provider_name=args.provider,
                model=model,
            )
            print(f"Generated enriched skill: {skill.name}")
        else:
            skill = generate_skill(llmstxt, name=args.name)
            print(f"Generated skill: {skill.name}")

        # Write or dry-run
        if args.dry_run:
            print("\n--- SKILL.md (dry-run) ---")
            print(skill.to_markdown())
        else:
            base_path = Path(args.output) if args.output else get_default_base_path()
            path = write_skill(skill, base_path=base_path, force=args.force)
            print(f"Written to: {path}")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Fetch error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileExistsError as e:
        print(f"File exists: {e}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        sys.exit(1)


def run() -> None:
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
