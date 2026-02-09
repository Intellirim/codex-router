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
        """Initialize configuration.

        Args:
            config_path: Path to config file
            data: Configuration dictionary
        """
        self.config_path = config_path
        self.data = data

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file.

        Args:
            config_path: Optional custom config path

        Returns:
            Config instance

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if config_path:
            path = Path(config_path)
        else:
            path = Path.home() / ".codex-router" / "config.yaml"

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
        """Initialize config with default values.

        Args:
            config_path: Optional custom config path

        Returns:
            New Config instance
        """
        if config_path:
            path = Path(config_path)
        else:
            path = Path.home() / ".codex-router" / "config.yaml"

        path.parent.mkdir(parents=True, exist_ok=True)

        data = cls.DEFAULT_CONFIG.copy()
        path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")

        return cls(path, data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            ValueError: If key is invalid
        """
        valid_keys = {
            "anthropic_api_key", "openai_api_key", "google_api_key",
            "default_model", "daily_budget", "max_parallel_agents"
        }

        if key not in valid_keys:
            raise ValueError(f"Invalid config key: {key}. Valid keys: {', '.join(valid_keys)}")

        if key == "daily_budget" or key == "max_parallel_agents":
            try:
                value = float(value) if key == "daily_budget" else int(value)
            except ValueError:
                raise ValueError(f"{key} must be a number")

            if value < 0:
                raise ValueError(f"{key} must be non-negative")

        self.data[key] = value

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.write_text(
            yaml.dump(self.data, default_flow_style=False),
            encoding="utf-8"
        )

    def validate(self) -> bool:
        """Check if at least one API key is configured.

        Returns:
            True if valid, False otherwise
        """
        api_keys = [
            self.data.get("anthropic_api_key"),
            self.data.get("openai_api_key"),
            self.data.get("google_api_key")
        ]

        return any(key and key.strip() for key in api_keys)
