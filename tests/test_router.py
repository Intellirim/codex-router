"""Unit tests for task routing logic."""

import pytest
from codex_router.router import TaskRouter
from codex_router.config import Config
from pathlib import Path
import tempfile


@pytest.fixture
def mock_config():
    """Create temporary config for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
anthropic_api_key: test_claude_key
openai_api_key: test_openai_key
google_api_key: test_google_key
default_model: claude
daily_budget: 10.0
max_parallel_agents: 5
""")
        config_path = f.name

    config = Config.load(config_path)
    yield config

    Path(config_path).unlink()


def test_analyze_complexity_high(mock_config):
    """Test high complexity task detection."""
    router = TaskRouter(mock_config)

    task = "refactor the entire authentication system and migrate to new framework"
    complexity = router.analyze_complexity(task)

    assert complexity == "high"


def test_analyze_complexity_medium(mock_config):
    """Test medium complexity task detection."""
    router = TaskRouter(mock_config)

    task = "add a new function to handle user registration"
    complexity = router.analyze_complexity(task)

    assert complexity == "medium"


def test_analyze_complexity_low(mock_config):
    """Test low complexity task detection."""
    router = TaskRouter(mock_config)

    task = "fix typo in documentation"
    complexity = router.analyze_complexity(task)

    assert complexity == "low"


def test_select_model_forced(mock_config):
    """Test forcing specific model selection."""
    router = TaskRouter(mock_config)

    task = "some task"
    model = router.select_model(task, force_model="gpt-4")

    assert model == "gpt-4"


def test_select_model_auto_high_complexity(mock_config):
    """Test automatic model selection for high complexity."""
    router = TaskRouter(mock_config)

    task = "refactor and optimize the entire codebase architecture"
    model = router.select_model(task)

    assert model == "claude-opus-4"


def test_select_model_auto_low_complexity(mock_config):
    """Test automatic model selection for low complexity."""
    router = TaskRouter(mock_config)

    task = "fix a simple typo"
    model = router.select_model(task)

    assert model == "gpt-3.5"


def test_select_model_invalid_forced(mock_config):
    """Test error on invalid forced model."""
    router = TaskRouter(mock_config)

    with pytest.raises(ValueError, match="Invalid model"):
        router.select_model("task", force_model="invalid-model")


def test_estimate_cost(mock_config):
    """Test cost estimation."""
    router = TaskRouter(mock_config)

    cost = router._estimate_cost("gpt-3.5", 1000)

    assert cost > 0
    assert isinstance(cost, float)


def test_calculate_cost(mock_config):
    """Test cost calculation."""
    router = TaskRouter(mock_config)

    cost = router._calculate_cost("claude", 2000)

    assert cost > 0
    assert isinstance(cost, float)


def test_validate_model_missing_api_key():
    """Test validation fails with missing API key."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
anthropic_api_key: ""
openai_api_key: ""
google_api_key: ""
default_model: claude
""")
        config_path = f.name

    config = Config.load(config_path)
    router = TaskRouter(config)

    with pytest.raises(ValueError, match="API key not configured"):
        router._validate_model_available("claude")

    Path(config_path).unlink()
