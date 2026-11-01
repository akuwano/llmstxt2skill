"""Fetcher for llms.txt files (URL or local file)."""

import os
from pathlib import Path

import httpx


def is_url(source: str) -> bool:
    """Check whether a source should be fetched over HTTP.

    Args:
        source: URL or local file path

    Returns:
        True if the source starts with http:// or https://
    """
    return source.lower().startswith(("http://", "https://"))


def read_llmstxt_file(path: str | os.PathLike) -> str:
    """Read llms.txt content from a local file.

    Args:
        path: Path to the local llms.txt file (read as UTF-8)

    Returns:
        Raw content of the llms.txt file

    Raises:
        ValueError: If the file cannot be read
    """
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        reason = e.strerror if isinstance(e, OSError) and e.strerror else str(e)
        raise ValueError(f"Cannot read {path}: {reason}") from e


async def fetch_llmstxt(url: str) -> str:
    """Fetch llms.txt content from a URL.

    Args:
        url: URL to fetch (e.g., https://docs.example.com/llms.txt)

    Returns:
        Raw content of the llms.txt file

    Raises:
        RuntimeError: If the fetch fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch {url}: HTTP {response.status_code}"
                )
            return response.text
    except httpx.RequestError as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}") from e
