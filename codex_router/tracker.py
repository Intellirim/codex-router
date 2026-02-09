"""Token usage and cost tracking with persistence."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List


class CostTracker:
    """Track and persist token usage and costs across providers."""

    def __init__(self, db_path: str = None):
        """Initialize cost tracker.

        Args:
            db_path: Optional custom database path
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".codex-router" / "usage.json"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.db_path.exists():
            self._init_db()

    def _init_db(self) -> None:
        """Initialize empty database."""
        data = {"records": []}
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record_usage(self, model: str, tokens: int, cost: float) -> None:
        """Record usage for a request.

        Args:
            model: Model identifier
            tokens: Token count
            cost: Cost in USD
        """
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"records": []}

        record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "tokens": tokens,
            "cost": cost
        }

        data["records"].append(record)

        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for time period.

        Args:
            days: Number of days to include

        Returns:
            Dictionary with aggregated statistics
        """
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "by_provider": {}
            }

        cutoff = datetime.now() - timedelta(days=days)
        records = data.get("records", [])

        filtered_records = [
            r for r in records
            if datetime.fromisoformat(r["timestamp"]) >= cutoff
        ]

        total_tokens = sum(r["tokens"] for r in filtered_records)
        total_cost = sum(r["cost"] for r in filtered_records)

        by_provider = {}
        for record in filtered_records:
            provider = self._get_provider_name(record["model"])
            if provider not in by_provider:
                by_provider[provider] = {"tokens": 0, "cost": 0.0, "requests": 0}

            by_provider[provider]["tokens"] += record["tokens"]
            by_provider[provider]["cost"] += record["cost"]
            by_provider[provider]["requests"] += 1

        return {
            "total_requests": len(filtered_records),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_provider": by_provider
        }

    def _get_provider_name(self, model: str) -> str:
        """Map model to provider name.

        Args:
            model: Model identifier

        Returns:
            Provider name
        """
        if "claude" in model.lower():
            return "Claude"
        elif "gpt" in model.lower():
            return "OpenAI"
        elif "gemini" in model.lower():
            return "Gemini"
        else:
            return "Unknown"

    def clear_old_records(self, days: int = 30) -> int:
        """Remove records older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of records removed
        """
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

        cutoff = datetime.now() - timedelta(days=days)
        records = data.get("records", [])

        original_count = len(records)
        filtered_records = [
            r for r in records
            if datetime.fromisoformat(r["timestamp"]) >= cutoff
        ]

        data["records"] = filtered_records
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        return original_count - len(filtered_records)
