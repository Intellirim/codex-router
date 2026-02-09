"""Unit tests for configuration management."""

import pytest
import tempfile
from pathlib import Path
from codex_router.config import Config


@pytest.fixture
def temp_config():
    """Create temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
anthropic_api_key: test_key_123
openai_api_key: test_key_456
google_api_key: test_key_789
default_model: claude
daily_budget: 10.0
max_parallel_agents: 5
""")
        config_path = f.name

    yield config_path

    Path(config_path).unlink(missing_ok=True)


def test_load_config(temp_config):
    """Test loading configuration from file."""
    config = Config.load(temp_config)

    assert config.get("anthropic_api_key") == "test_key_123"
    assert config.get("openai_api_key") == "test_key_456"
    assert config.get("default_model") == "claude"
    assert config.get("daily_budget") == 10.0


def test_load_config_not_found():
    """Test error when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        Config.load("/nonexistent/path/config.yaml")


def test_init_default_config():
    """Test initializing default configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        config = Config.init_default(str(config_path))

        assert config_path.exists()
        assert config.get("default_model") == "claude"
        assert config.get("daily_budget") == 10.0
        assert config.get("anthropic_api_key") == ""


def test_get_with_default(temp_config):
    """Test getting value with default fallback."""
    config = Config.load(temp_config)

    value = config.get("nonexistent_key", "default_value")

    assert value == "default_value"


def test_get_existing_key(temp_config):
    """Test getting existing configuration value."""
    config = Config.load(temp_config)

    value = config.get("default_model")

    assert value == "claude"


def test_set_valid_key(temp_config):
    """Test setting valid configuration key."""
    config = Config.load(temp_config)

    config.set("default_model", "gpt-4")

    assert config.get("default_model") == "gpt-4"


def test_set_invalid_key(temp_config):
    """Test error when setting invalid key."""
    config = Config.load(temp_config)

    with pytest.raises(ValueError, match="Invalid config key"):
        config.set("invalid_key", "value")


def test_set_budget_validation(temp_config):
    """Test budget value validation."""
    config = Config.load(temp_config)

    config.set("daily_budget", "15.50")
    assert config.get("daily_budget") == 15.50

    with pytest.raises(ValueError, match="must be a number"):
        config.set("daily_budget", "not_a_number")

    with pytest.raises(ValueError, match="must be non-negative"):
        config.set("daily_budget", "-5")


def test_save_config(temp_config):
    """Test saving configuration to file."""
    config = Config.load(temp_config)

    config.set("default_model", "gpt-4")
    config.save()

    reloaded = Config.load(temp_config)
    assert reloaded.get("default_model") == "gpt-4"


def test_validate_with_keys(temp_config):
    """Test validation with API keys present."""
    config = Config.load(temp_config)

    assert config.validate() is True


def test_validate_without_keys():
    """Test validation without API keys."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
anthropic_api_key: ""
openai_api_key: ""
google_api_key: ""
default_model: claude
""")
        config_path = f.name

    config = Config.load(config_path)

    assert config.validate() is False

    Path(config_path).unlink()


def test_set_max_parallel_agents(temp_config):
    """Test setting max parallel agents."""
    config = Config.load(temp_config)

    config.set("max_parallel_agents", "10")
    assert config.get("max_parallel_agents") == 10

    with pytest.raises(ValueError):
        config.set("max_parallel_agents", "not_a_number")
