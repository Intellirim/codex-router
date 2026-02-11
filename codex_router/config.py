"""Configuration management for API keys, defaults, and budgets."""

import yaml
from pathlib import Path
from typing import Any, Optional


class Config:
    """Manage configuration file with API keys and preferences."""

    DEFAULT_CONFIG = {
        "anthropic_api_key": "",
        "openai_api_key": "",
        "google_api_key": "",
        "default_model": "claude",
        "daily_budget": 10.0,
        "max_parallel_agents": 5
    }

    def __init__(self, config_path: Path, data: dict):
        """Initialize configuration."""
        self.config_path = config_path
        self.data = data

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file."""
        path = Path(config_path) if config_path else Path.home() / ".codex-router" / "config.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config: {str(e)}")
        if not isinstance(data, dict):
            raise ValueError("Config must be a YAML dictionary")
        return cls(path, data)

    @classmethod
    def init_default(cls, config_path: Optional[str] = None) -> "Config":
        """Initialize config with default values."""
        path = Path(config_path) if config_path else Path.home() / ".codex-router" / "config.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = cls.DEFAULT_CONFIG.copy()
        path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
        return cls(path, data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        valid = {"anthropic_api_key", "openai_api_key", "google_api_key", "default_model", "daily_budget", "max_parallel_agents"}
        if key not in valid:
            raise ValueError(f"Invalid config key: {key}. Valid keys: {', '.join(valid)}")
        if key in ["daily_budget", "max_parallel_agents"]:
            try:
                value = float(value) if key == "daily_budget" else int(value)
            except ValueError:
                raise ValueError(f"{key} must be a number")
            if value < 0:
                raise ValueError(f"{key} must be non-negative")
        self.data[key] = value

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.write_text(yaml.dump(self.data, default_flow_style=False), encoding="utf-8")

    def validate(self) -> bool:
        """Check if at least one API key is configured."""
        return any(k and k.strip() for k in [self.data.get("anthropic_api_key"), self.data.get("openai_api_key"), self.data.get("google_api_key")])
