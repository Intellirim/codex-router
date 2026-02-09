"""Unified interface for Claude, OpenAI, and Gemini APIs."""

from typing import Dict, Any, Protocol
from codex_router.config import Config


class Provider(Protocol):
    """Protocol for AI provider implementations."""

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task and return result with token count."""
        ...


class ClaudeProvider:
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier
        """
        self.api_key = api_key
        self.model = model

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task using Claude API.

        Args:
            task: Task description

        Returns:
            Dictionary with output and token count
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": task}]
            )

            output = message.content[0].text
            tokens = message.usage.input_tokens + message.usage.output_tokens

            return {"output": output, "tokens": tokens}
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")


class OpenAIProvider:
    """OpenAI GPT API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: GPT model identifier
        """
        self.api_key = api_key
        self.model = model

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task using OpenAI API.

        Args:
            task: Task description

        Returns:
            Dictionary with output and token count
        """
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        client = openai.OpenAI(api_key=self.api_key)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": task}],
                max_tokens=4000
            )

            output = response.choices[0].message.content
            tokens = response.usage.total_tokens

            return {"output": output, "tokens": tokens}
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class GeminiProvider:
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Gemini model identifier
        """
        self.api_key = api_key
        self.model = model

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task using Gemini API.

        Args:
            task: Task description

        Returns:
            Dictionary with output and token count
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package required")

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        try:
            response = model.generate_content(task)
            output = response.text
            tokens = len(task.split()) + len(output.split())

            return {"output": output, "tokens": tokens}
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")


def get_provider(model: str, config: Config) -> Provider:
    """Get appropriate provider for model.

    Args:
        model: Model identifier
        config: Configuration object

    Returns:
        Provider instance

    Raises:
        ValueError: If model unknown or API key missing
    """
    provider_map = {
        "claude": ("anthropic_api_key", ClaudeProvider, "claude-3-5-sonnet-20241022"),
        "claude-opus-4": ("anthropic_api_key", ClaudeProvider, "claude-opus-4-20250514"),
        "gpt-4": ("openai_api_key", OpenAIProvider, "gpt-4"),
        "gpt-3.5": ("openai_api_key", OpenAIProvider, "gpt-3.5-turbo"),
        "gemini": ("google_api_key", GeminiProvider, "gemini-pro"),
    }

    if model not in provider_map:
        raise ValueError(f"Unknown model: {model}")

    key_name, provider_class, api_model = provider_map[model]
    api_key = config.get(key_name)

    if not api_key:
        raise ValueError(f"API key not configured: {key_name}")

    return provider_class(api_key, api_model)
