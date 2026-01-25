"""Tests for LLM providers."""

import pytest

from llmstxt2skill.llm.base import LLMRequest
from llmstxt2skill.llm.factory import (
    create_provider,
    get_default_model,
    list_providers,
)
from llmstxt2skill.llm.providers.anthropic import AnthropicProvider
from llmstxt2skill.llm.providers.databricks import DatabricksProvider
from llmstxt2skill.llm.providers.openai import OpenAIProvider
from llmstxt2skill.llm.providers.openai_compatible import OpenAICompatibleProvider


class TestLLMRequest:
    """Tests for LLMRequest dataclass."""

    def test_create_request(self) -> None:
        """Should create request with required fields."""
        request = LLMRequest(prompt="Hello", model="test-model")
        assert request.prompt == "Hello"
        assert request.model == "test-model"
        assert request.max_tokens == 4000
        assert request.temperature == 0.2
        assert request.system is None

    def test_create_request_with_all_fields(self) -> None:
        """Should create request with all fields."""
        request = LLMRequest(
            prompt="Hello",
            model="test-model",
            max_tokens=1000,
            temperature=0.5,
            system="You are helpful",
        )
        assert request.max_tokens == 1000
        assert request.temperature == 0.5
        assert request.system == "You are helpful"


class TestFactory:
    """Tests for provider factory."""

    def test_list_providers(self) -> None:
        """Should list available providers."""
        providers = list_providers()
        assert "databricks" in providers
        assert "openai" in providers
        assert "anthropic" in providers
        assert "openai-compatible" in providers

    def test_get_default_model(self) -> None:
        """Should return default model for each provider."""
        assert get_default_model("databricks") == "databricks-gemini-3-pro"
        assert get_default_model("openai") == "gpt-4o-mini"
        assert get_default_model("anthropic") == "claude-3-5-sonnet-20241022"

    def test_get_default_model_unknown(self) -> None:
        """Should return 'default' for unknown provider."""
        assert get_default_model("unknown") == "default"

    def test_create_provider_unknown(self) -> None:
        """Should raise error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("unknown-provider")


class TestDatabricksProvider:
    """Tests for DatabricksProvider."""

    def test_init_without_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error when credentials not set."""
        monkeypatch.delenv("DATABRICKS_HOST", raising=False)
        monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
        with pytest.raises(ValueError, match="DATABRICKS_HOST"):
            DatabricksProvider()

    def test_init_with_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should initialize with environment variables."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")
        provider = DatabricksProvider()
        assert provider.host == "https://test.databricks.com"
        assert provider.token == "test-token"

    def test_init_with_explicit_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use explicit credentials over env vars."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://env.databricks.com")
        monkeypatch.setenv("DATABRICKS_TOKEN", "env-token")
        provider = DatabricksProvider(
            host="https://explicit.databricks.com", token="explicit-token"
        )
        assert provider.host == "https://explicit.databricks.com"
        assert provider.token == "explicit-token"


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_init_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error when API key not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            OpenAIProvider()

    def test_init_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should initialize with environment variable."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        provider = OpenAIProvider()
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.openai.com"

    def test_init_with_custom_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should use custom base URL."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.openai.com")
        provider = OpenAIProvider()
        assert provider.base_url == "https://custom.openai.com"


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_init_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise error when API key not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AnthropicProvider()

    def test_init_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should initialize with environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider()
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.anthropic.com"


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""

    def test_init_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should use default localhost URL."""
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAICompatibleProvider()
        assert provider.base_url == "http://localhost:8000"
        assert provider.api_key == ""

    def test_init_with_custom_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should use custom base URL."""
        monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434")
        provider = OpenAICompatibleProvider()
        assert provider.base_url == "http://localhost:11434"

    def test_init_with_optional_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should work with optional API key."""
        monkeypatch.setenv("OPENAI_API_KEY", "optional-key")
        provider = OpenAICompatibleProvider()
        assert provider.api_key == "optional-key"
