"""URL fetcher for llms.txt files."""

import httpx


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
