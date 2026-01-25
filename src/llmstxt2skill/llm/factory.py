"""Factory for creating LLM providers."""

from llmstxt2skill.llm.base import LLMProvider
from llmstxt2skill.llm.providers.anthropic import AnthropicProvider
from llmstxt2skill.llm.providers.databricks import DatabricksProvider
from llmstxt2skill.llm.providers.openai import OpenAIProvider
from llmstxt2skill.llm.providers.openai_compatible import OpenAICompatibleProvider

# Provider name to class mapping
PROVIDERS: dict[str, type] = {
    "databricks": DatabricksProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "openai-compatible": OpenAICompatibleProvider,
}

# Default models for each provider
DEFAULT_MODELS: dict[str, str] = {
    "databricks": "databricks-gemini-3-pro",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openai-compatible": "default",
}


def create_provider(provider_name: str) -> LLMProvider:
    """Create an LLM provider by name.

    Args:
        provider_name: Name of the provider (databricks, openai, anthropic, openai-compatible)

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider_name is not recognized
    """
    provider_class = PROVIDERS.get(provider_name)
    if provider_class is None:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. Available providers: {available}"
        )
    return provider_class()


def get_default_model(provider_name: str) -> str:
    """Get the default model for a provider.

    Args:
        provider_name: Name of the provider

    Returns:
        Default model identifier for the provider
    """
    return DEFAULT_MODELS.get(provider_name, "default")


def list_providers() -> list[str]:
    """List available provider names.

    Returns:
        List of provider names
    """
    return list(PROVIDERS.keys())
