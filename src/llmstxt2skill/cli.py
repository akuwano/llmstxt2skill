"""CLI entry point for llmstxt2skill."""

import argparse
import asyncio
import sys
from pathlib import Path

from llmstxt2skill.fetcher import fetch_llmstxt
from llmstxt2skill.generator import generate_skill
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
        "--dry-run",
        action="store_true",
        help="Print output without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing skill",
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

        # Generate
        skill = generate_skill(llmstxt, name=args.name)
        print(f"Generated skill: {skill.name}")

        # Write or dry-run
        if args.dry_run:
            print("\n--- SKILL.md (dry-run) ---")
            print(skill.to_markdown())
        else:
            base_path = get_default_base_path()
            path = write_skill(skill, base_path=base_path, force=args.force)
            print(f"Written to: {path}")

    except ValueError as e:
        print(f"Parse error: {e}", file=sys.stderr)
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
