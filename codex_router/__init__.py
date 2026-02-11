"""codex-router: Intelligent routing and orchestration for multi-model AI coding agents."""

__version__ = "0.2.0"
__author__ = "Intellirim"
__license__ = "MIT"

from codex_router.router import TaskRouter
from codex_router.config import Config
from codex_router.tracker import CostTracker

__all__ = ["TaskRouter", "Config", "CostTracker", "__version__"]
