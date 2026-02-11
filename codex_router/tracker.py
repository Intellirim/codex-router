"""Token usage and cost tracking with persistence."""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List


class CostTracker:
    """Track and persist token usage and costs across providers."""

    def __init__(self, db_path: str = None):
        """Initialize cost tracker."""
        self.db_path = Path(db_path) if db_path else Path.home() / ".codex-router" / "usage.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self._init_db()

    def _init_db(self) -> None:
        """Initialize empty database."""
        self.db_path.write_text(json.dumps({"records": []}, indent=2), encoding="utf-8")

    def record_usage(self, model: str, tokens: int, cost: float) -> None:
        """Record usage for a request."""
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"records": []}
        data["records"].append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "tokens": tokens,
            "cost": cost
        })
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for time period."""
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total_requests": 0, "total_tokens": 0, "total_cost": 0.0, "by_provider": {}}

        cutoff = datetime.now() - timedelta(days=days)
        filtered_records = [r for r in data.get("records", []) if datetime.fromisoformat(r["timestamp"]) >= cutoff]

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
            "total_tokens": sum(r["tokens"] for r in filtered_records),
            "total_cost": sum(r["cost"] for r in filtered_records),
            "by_provider": by_provider
        }

    def _get_provider_name(self, model: str) -> str:
        """Map model to provider name."""
        m = model.lower()
        return "Claude" if "claude" in m else "OpenAI" if "gpt" in m else "Gemini" if "gemini" in m else "Unknown"

    def clear_old_records(self, days: int = 30) -> int:
        """Remove records older than specified days."""
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
        cutoff = datetime.now() - timedelta(days=days)
        records = data.get("records", [])
        filtered = [r for r in records if datetime.fromisoformat(r["timestamp"]) >= cutoff]
        data["records"] = filtered
        self.db_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return len(records) - len(filtered)
