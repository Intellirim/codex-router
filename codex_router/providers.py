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
        """Initialize Claude provider."""
        self.api_key = api_key
        self.model = model

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task using Claude API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")
        client = anthropic.Anthropic(api_key=self.api_key)
        try:
            message = client.messages.create(model=self.model, max_tokens=4000, messages=[{"role": "user", "content": task}])
            return {"output": message.content[0].text, "tokens": message.usage.input_tokens + message.usage.output_tokens}
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")


class OpenAIProvider:
    """OpenAI GPT API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize OpenAI provider."""
        self.api_key = api_key
        self.model = model

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task using OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")
        client = openai.OpenAI(api_key=self.api_key)
        try:
            response = client.chat.completions.create(model=self.model, messages=[{"role": "user", "content": task}], max_tokens=4000)
            return {"output": response.choices[0].message.content, "tokens": response.usage.total_tokens}
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class GeminiProvider:
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """Initialize Gemini provider."""
        self.api_key = api_key
        self.model = model

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute task using Gemini API."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package required")
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        try:
            response = model.generate_content(task)
            return {"output": response.text, "tokens": len(task.split()) + len(response.text.split())}
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")


def get_provider(model: str, config: Config) -> Provider:
    """Get appropriate provider for model."""
    pmap = {"claude": ("anthropic_api_key", ClaudeProvider, "claude-3-5-sonnet-20241022"), "claude-opus-4": ("anthropic_api_key", ClaudeProvider, "claude-opus-4-20250514"), "gpt-4": ("openai_api_key", OpenAIProvider, "gpt-4"), "gpt-3.5": ("openai_api_key", OpenAIProvider, "gpt-3.5-turbo"), "gemini": ("google_api_key", GeminiProvider, "gemini-pro")}
    if model not in pmap:
        raise ValueError(f"Unknown model: {model}")
    key_name, provider_class, api_model = pmap[model]
    api_key = config.get(key_name)
    if not api_key:
        raise ValueError(f"API key not configured: {key_name}")
    return provider_class(api_key, api_model)
