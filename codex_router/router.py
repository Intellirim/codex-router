"""Task analysis and intelligent model selection."""

import re
from typing import Optional, Dict, Any
from codex_router.config import Config
from codex_router.providers import get_provider


class TaskRouter:
    """Routes tasks to optimal AI model based on complexity analysis."""

    COMPLEXITY_KEYWORDS = {
        "high": [
            "refactor", "architect", "design", "implement", "migrate", "optimize",
            "complex", "entire", "system", "framework", "multi", "integrate"
        ],
        "medium": [
            "add", "create", "modify", "update", "enhance", "improve",
            "feature", "function", "class", "module", "api"
        ],
        "low": [
            "fix", "typo", "rename", "format", "comment", "document",
            "simple", "small", "quick", "minor", "single"
        ]
    }

    MODEL_COSTS = {
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude": {"input": 3.0, "output": 15.0},
        "gpt-4": {"input": 10.0, "output": 30.0},
        "gpt-3.5": {"input": 0.5, "output": 1.5},
        "gemini": {"input": 0.0, "output": 0.0},
    }

    def __init__(self, config: Config):
        """Initialize router with configuration.

        Args:
            config: Configuration object with API keys and preferences
        """
        self.config = config

    def analyze_complexity(self, task: str) -> str:
        """Analyze task description to determine complexity.

        Args:
            task: Task description string

        Returns:
            Complexity level: "high", "medium", or "low"
        """
        task_lower = task.lower()
        scores = {"high": 0, "medium": 0, "low": 0}

        for level, keywords in self.COMPLEXITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    scores[level] += 1

        if scores["high"] > 0:
            return "high"
        elif scores["medium"] > scores["low"]:
            return "medium"
        else:
            return "low"

    def select_model(self, task: str, force_model: Optional[str] = None) -> str:
        """Select optimal model based on task complexity and config.

        Args:
            task: Task description
            force_model: Override automatic selection with specific model

        Returns:
            Selected model identifier

        Raises:
            ValueError: If forced model is invalid or API key missing
        """
        if force_model:
            if force_model not in self.MODEL_COSTS:
                raise ValueError(f"Invalid model: {force_model}")
            self._validate_model_available(force_model)
            return force_model

        complexity = self.analyze_complexity(task)
        default_model = self.config.get("default_model", "claude")

        complexity_mapping = {
            "high": "claude-opus-4",
            "medium": default_model,
            "low": "gpt-3.5"
        }

        selected = complexity_mapping[complexity]

        try:
            self._validate_model_available(selected)
            return selected
        except ValueError:
            fallback = "gpt-3.5"
            self._validate_model_available(fallback)
            return fallback

    def _validate_model_available(self, model: str) -> None:
        """Check if API key exists for model.

        Args:
            model: Model identifier

        Raises:
            ValueError: If API key not configured
        """
        provider_map = {
            "claude": "anthropic_api_key",
            "claude-opus-4": "anthropic_api_key",
            "gpt-4": "openai_api_key",
            "gpt-3.5": "openai_api_key",
            "gemini": "google_api_key"
        }

        key_name = provider_map.get(model)
        if not key_name:
            raise ValueError(f"Unknown model: {model}")

        if not self.config.get(key_name):
            raise ValueError(f"API key not configured: {key_name}")

    def execute_task(self, task: str, model: str, budget: Optional[float] = None) -> Dict[str, Any]:
        """Execute task using selected model.

        Args:
            task: Task description
            model: Model to use
            budget: Optional budget limit in USD

        Returns:
            Dictionary with output, tokens used, and cost

        Raises:
            ValueError: If budget exceeded or execution fails
        """
        provider = get_provider(model, self.config)

        estimated_tokens = len(task.split()) * 3
        estimated_cost = self._estimate_cost(model, estimated_tokens)

        if budget and estimated_cost > budget:
            raise ValueError(f"Estimated cost ${estimated_cost:.3f} exceeds budget ${budget:.2f}")

        try:
            result = provider.execute(task)
            return {
                "output": result["output"],
                "tokens": result["tokens"],
                "cost": self._calculate_cost(model, result["tokens"])
            }
        except Exception as e:
            raise ValueError(f"Execution failed: {str(e)}")

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for token count.

        Args:
            model: Model identifier
            tokens: Estimated token count

        Returns:
            Estimated cost in USD
        """
        costs = self.MODEL_COSTS.get(model, {"input": 1.0, "output": 1.0})
        return (tokens * costs["input"] / 1_000_000) + (tokens * costs["output"] / 1_000_000)

    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate actual cost for completed request.

        Args:
            model: Model identifier
            tokens: Actual token count

        Returns:
            Cost in USD
        """
        return self._estimate_cost(model, tokens)
