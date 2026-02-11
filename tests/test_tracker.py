"""Unit tests for cost tracking."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from codex_router.tracker import CostTracker


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        db_path = f.name

    yield db_path

    Path(db_path).unlink(missing_ok=True)


def test_init_creates_database(temp_db):
    """Test database initialization."""
    Path(temp_db).unlink(missing_ok=True)
    tracker = CostTracker(temp_db)

    assert Path(temp_db).exists()

    data = json.loads(Path(temp_db).read_text())
    assert "records" in data
    assert data["records"] == []


def test_record_usage(temp_db):
    """Test recording usage data."""
    tracker = CostTracker(temp_db)

    tracker.record_usage("claude", 1000, 0.05)

    data = json.loads(Path(temp_db).read_text())
    assert len(data["records"]) == 1

    record = data["records"][0]
    assert record["model"] == "claude"
    assert record["tokens"] == 1000
    assert record["cost"] == 0.05
    assert "timestamp" in record


def test_record_multiple_usage(temp_db):
    """Test recording multiple usage records."""
    tracker = CostTracker(temp_db)

    tracker.record_usage("claude", 1000, 0.05)
    tracker.record_usage("gpt-4", 2000, 0.10)
    tracker.record_usage("gemini", 500, 0.00)

    data = json.loads(Path(temp_db).read_text())
    assert len(data["records"]) == 3
    assert all("timestamp" in r for r in data["records"])


def test_get_stats_empty(temp_db):
    """Test statistics with empty database."""
    tracker = CostTracker(temp_db)

    stats = tracker.get_stats(7)

    assert stats["total_requests"] == 0
    assert stats["total_tokens"] == 0
    assert stats["total_cost"] == 0.0
    assert stats["by_provider"] == {}


def test_get_stats_with_data(temp_db):
    """Test statistics calculation with data."""
    tracker = CostTracker(temp_db)

    tracker.record_usage("claude", 1000, 0.05)
    tracker.record_usage("gpt-4", 2000, 0.10)
    tracker.record_usage("claude", 500, 0.025)

    stats = tracker.get_stats(7)

    assert stats["total_requests"] == 3
    assert stats["total_tokens"] == 3500
    assert abs(stats["total_cost"] - 0.175) < 0.001

    assert "Claude" in stats["by_provider"]
    assert stats["by_provider"]["Claude"]["tokens"] == 1500
    assert abs(stats["by_provider"]["Claude"]["cost"] - 0.075) < 0.001


def test_get_stats_time_filter(temp_db):
    """Test filtering records by time period."""
    tracker = CostTracker(temp_db)

    old_timestamp = (datetime.now() - timedelta(days=10)).isoformat()
    recent_timestamp = datetime.now().isoformat()

    data = {
        "records": [
            {"timestamp": old_timestamp, "model": "claude", "tokens": 1000, "cost": 0.05},
            {"timestamp": recent_timestamp, "model": "gpt-4", "tokens": 2000, "cost": 0.10}
        ]
    }

    Path(temp_db).write_text(json.dumps(data))

    stats = tracker.get_stats(7)

    assert stats["total_requests"] == 1
    assert stats["total_tokens"] == 2000
    assert stats["total_cost"] == 0.10


def test_get_provider_name(temp_db):
    """Test provider name mapping."""
    tracker = CostTracker(temp_db)

    assert tracker._get_provider_name("claude-opus-4") == "Claude"
    assert tracker._get_provider_name("gpt-4") == "OpenAI"
    assert tracker._get_provider_name("gemini-pro") == "Gemini"
    assert tracker._get_provider_name("unknown-model") == "Unknown"


def test_clear_old_records(temp_db):
    """Test clearing old records."""
    tracker = CostTracker(temp_db)

    old_timestamp = (datetime.now() - timedelta(days=40)).isoformat()
    recent_timestamp = datetime.now().isoformat()

    data = {
        "records": [
            {"timestamp": old_timestamp, "model": "claude", "tokens": 1000, "cost": 0.05},
            {"timestamp": recent_timestamp, "model": "gpt-4", "tokens": 2000, "cost": 0.10}
        ]
    }

    Path(temp_db).write_text(json.dumps(data))

    removed = tracker.clear_old_records(30)

    assert removed == 1

    data = json.loads(Path(temp_db).read_text())
    assert len(data["records"]) == 1
    assert data["records"][0]["model"] == "gpt-4"
