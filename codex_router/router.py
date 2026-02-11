"""Task analysis and intelligent model selection."""

import re
from typing import Optional, Dict, Any
from codex_router.config import Config
from codex_router.providers import get_provider


class TaskRouter:
    """Routes tasks to optimal AI model based on complexity analysis."""

    COMPLEXITY_KEYWORDS = {
        "high": ["refactor", "architect", "design", "migrate", "complex", "entire", "system", "framework"],
        "medium": ["add", "create", "modify", "update", "enhance", "feature", "function", "module"],
        "low": ["fix", "typo", "rename", "format", "comment", "simple", "quick", "minor"]
    }

    MODEL_COSTS = {
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude": {"input": 3.0, "output": 15.0},
        "gpt-4": {"input": 10.0, "output": 30.0},
        "gpt-3.5": {"input": 0.5, "output": 1.5},
        "gemini": {"input": 0.0, "output": 0.0},
    }

    def __init__(self, config: Config):
        """Initialize router with configuration."""
        self.config = config

    def analyze_complexity(self, task: str) -> str:
        """Analyze task description to determine complexity."""
        task_lower = task.lower()
        scores = {"high": 0, "medium": 0, "low": 0}
        for level, keywords in self.COMPLEXITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    scores[level] += 1
        return "high" if scores["high"] > 0 else "medium" if scores["medium"] > scores["low"] else "low"

    def select_model(self, task: str, force_model: Optional[str] = None) -> str:
        """Select optimal model based on task complexity and config."""
        if force_model:
            if force_model not in self.MODEL_COSTS:
                raise ValueError(f"Invalid model: {force_model}")
            self._validate_model_available(force_model)
            return force_model
        complexity = self.analyze_complexity(task)
        mapping = {"high": "claude-opus-4", "medium": self.config.get("default_model", "claude"), "low": "gpt-3.5"}
        selected = mapping[complexity]
        try:
            self._validate_model_available(selected)
            return selected
        except ValueError:
            self._validate_model_available("gpt-3.5")
            return "gpt-3.5"

    def _validate_model_available(self, model: str) -> None:
        """Check if API key exists for model."""
        pmap = {"claude": "anthropic_api_key", "claude-opus-4": "anthropic_api_key", "gpt-4": "openai_api_key", "gpt-3.5": "openai_api_key", "gemini": "google_api_key"}
        key_name = pmap.get(model)
        if not key_name:
            raise ValueError(f"Unknown model: {model}")
        if not self.config.get(key_name):
            raise ValueError(f"API key not configured: {key_name}")

    def execute_task(self, task: str, model: str, budget: Optional[float] = None) -> Dict[str, Any]:
        """Execute task using selected model."""
        provider = get_provider(model, self.config)
        estimated_cost = self._estimate_cost(model, len(task.split()) * 3)
        if budget and estimated_cost > budget:
            raise ValueError(f"Estimated cost ${estimated_cost:.3f} exceeds budget ${budget:.2f}")
        try:
            result = provider.execute(task)
            return {"output": result["output"], "tokens": result["tokens"], "cost": self._calculate_cost(model, result["tokens"])}
        except Exception as e:
            raise ValueError(f"Execution failed: {str(e)}")

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for token count."""
        costs = self.MODEL_COSTS.get(model, {"input": 1.0, "output": 1.0})
        return (tokens * costs["input"] / 1_000_000) + (tokens * costs["output"] / 1_000_000)

    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate actual cost for completed request."""
        return self._estimate_cost(model, tokens)
