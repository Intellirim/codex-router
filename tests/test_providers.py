"""Mock tests for provider interfaces."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from codex_router.providers import ClaudeProvider, OpenAIProvider, GeminiProvider, get_provider
from codex_router.config import Config
import tempfile
from pathlib import Path


@pytest.fixture
def mock_config():
    """Create mock config for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
anthropic_api_key: test_claude_key
openai_api_key: test_openai_key
google_api_key: test_google_key
default_model: claude
""")
        config_path = f.name

    config = Config.load(config_path)
    yield config

    Path(config_path).unlink()


def test_claude_provider_init():
    """Test Claude provider initialization."""
    provider = ClaudeProvider("test_key", "claude-3-5-sonnet-20241022")

    assert provider.api_key == "test_key"
    assert provider.model == "claude-3-5-sonnet-20241022"


def test_openai_provider_init():
    """Test OpenAI provider initialization."""
    provider = OpenAIProvider("test_key", "gpt-4")

    assert provider.api_key == "test_key"
    assert provider.model == "gpt-4"


def test_gemini_provider_init():
    """Test Gemini provider initialization."""
    provider = GeminiProvider("test_key", "gemini-pro")

    assert provider.api_key == "test_key"
    assert provider.model == "gemini-pro"


@patch("codex_router.providers.anthropic.Anthropic")
def test_claude_provider_execute(mock_anthropic_class):
    """Test Claude provider execution with mocked API."""
    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    mock_message = Mock()
    mock_message.content = [Mock(text="Test response")]
    mock_message.usage = Mock(input_tokens=100, output_tokens=200)

    mock_client.messages.create.return_value = mock_message

    provider = ClaudeProvider("test_key")
    result = provider.execute("test task")

    assert result["output"] == "Test response"
    assert result["tokens"] == 300
    mock_client.messages.create.assert_called_once()


@patch("codex_router.providers.openai.OpenAI")
def test_openai_provider_execute(mock_openai_class):
    """Test OpenAI provider execution with mocked API."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_response.usage = Mock(total_tokens=500)

    mock_client.chat.completions.create.return_value = mock_response

    provider = OpenAIProvider("test_key")
    result = provider.execute("test task")

    assert result["output"] == "Test response"
    assert result["tokens"] == 500
    mock_client.chat.completions.create.assert_called_once()


@patch("codex_router.providers.genai.configure")
@patch("codex_router.providers.genai.GenerativeModel")
def test_gemini_provider_execute(mock_model_class, mock_configure):
    """Test Gemini provider execution with mocked API."""
    mock_model = Mock()
    mock_model_class.return_value = mock_model

    mock_response = Mock(text="Test response")
    mock_model.generate_content.return_value = mock_response

    provider = GeminiProvider("test_key")
    result = provider.execute("test task")

    assert result["output"] == "Test response"
    assert result["tokens"] > 0
    mock_configure.assert_called_once_with(api_key="test_key")
    mock_model.generate_content.assert_called_once()


def test_get_provider_claude(mock_config):
    """Test getting Claude provider."""
    provider = get_provider("claude", mock_config)

    assert isinstance(provider, ClaudeProvider)
    assert provider.api_key == "test_claude_key"


def test_get_provider_openai(mock_config):
    """Test getting OpenAI provider."""
    provider = get_provider("gpt-4", mock_config)

    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "test_openai_key"
    assert provider.model == "gpt-4"


def test_get_provider_gemini(mock_config):
    """Test getting Gemini provider."""
    provider = get_provider("gemini", mock_config)

    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "test_google_key"


def test_get_provider_invalid_model(mock_config):
    """Test error on invalid model."""
    with pytest.raises(ValueError, match="Unknown model"):
        get_provider("invalid-model", mock_config)


def test_get_provider_missing_api_key():
    """Test error when API key missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
anthropic_api_key: ""
openai_api_key: ""
google_api_key: ""
default_model: claude
""")
        config_path = f.name

    config = Config.load(config_path)

    with pytest.raises(ValueError, match="API key not configured"):
        get_provider("claude", config)

    Path(config_path).unlink()


@patch("codex_router.providers.anthropic.Anthropic")
def test_claude_provider_api_error(mock_anthropic_class):
    """Test Claude provider handling API errors."""
    mock_client = Mock()
    mock_anthropic_class.return_value = mock_client

    mock_client.messages.create.side_effect = Exception("API Error")

    provider = ClaudeProvider("test_key")

    with pytest.raises(RuntimeError, match="Claude API error"):
        provider.execute("test task")
