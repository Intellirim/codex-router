"""Terminal output formatting with ASCII-safe, cross-platform support."""

import sys
from typing import Dict, Any


class Display:
    """Handle terminal output with ASCII-only formatting."""

    def __init__(self):
        """Initialize display handler."""
        pass

    def info(self, message: str) -> None:
        """Display info message.

        Args:
            message: Message to display
        """
        print(f"[Router] {message}")

    def success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Message to display
        """
        print(f"[Router] {message}")

    def error(self, message: str) -> None:
        """Display error message to stderr.

        Args:
            message: Error message
        """
        print(f"[ERROR] {message}", file=sys.stderr)

    def agent_start(self, agent_id: int, model: str) -> None:
        """Display agent start message.

        Args:
            agent_id: Agent identifier
            model: Model being used
        """
        print(f"[Agent-{agent_id}] Starting with model: {model}")

    def agent_complete(self, agent_id: int, tokens: int, cost: float) -> None:
        """Display agent completion message.

        Args:
            agent_id: Agent identifier
            tokens: Tokens used
            cost: Cost in USD
        """
        print(f"[Agent-{agent_id}] DONE - {tokens} tokens (${cost:.3f})")

    def show_result(self, output: str) -> None:
        """Display task result output.

        Args:
            output: Result text
        """
        print("\n--- Result ---")
        print(output)
        print("--- End ---\n")

    def show_cost_table(self, stats: Dict[str, Any], days: int) -> None:
        """Display cost statistics table.

        Args:
            stats: Statistics dictionary
            days: Number of days covered
        """
        print(f"\nToken Usage Summary (Last {days} Days)")
        print("-" * 45)
        print(f"{'Provider':<12} | {'Tokens':<10} | {'Cost'}")
        print("-" * 45)

        by_provider = stats.get("by_provider", {})

        for provider, data in sorted(by_provider.items()):
            tokens = data.get("tokens", 0)
            cost = data.get("cost", 0.0)
            print(f"{provider:<12} | {tokens:<10,} | ${cost:.2f}")

        print("-" * 45)
        total_cost = stats.get("total_cost", 0.0)
        print(f"{'Total':<12} | {'':<10} | ${total_cost:.2f}")
        print()

    def warning(self, message: str) -> None:
        """Display warning message.

        Args:
            message: Warning message
        """
        print(f"[WARNING] {message}", file=sys.stderr)

    def debug(self, message: str) -> None:
        """Display debug message.

        Args:
            message: Debug message
        """
        print(f"[DEBUG] {message}")
