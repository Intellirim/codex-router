"""Terminal output formatting with ASCII-safe, cross-platform support."""

import sys
from typing import Dict, Any


class Display:
    """Handle terminal output with ASCII-only formatting."""

    def info(self, message: str) -> None:
        """Display info message."""
        print(f"[Router] {message}")

    def success(self, message: str) -> None:
        """Display success message."""
        print(f"[Router] {message}")

    def error(self, message: str) -> None:
        """Display error message to stderr."""
        print(f"[ERROR] {message}", file=sys.stderr)

    def agent_start(self, agent_id: int, model: str) -> None:
        """Display agent start message."""
        print(f"[Agent-{agent_id}] Starting with model: {model}")

    def agent_complete(self, agent_id: int, tokens: int, cost: float) -> None:
        """Display agent completion message."""
        print(f"[Agent-{agent_id}] DONE - {tokens} tokens (${cost:.3f})")

    def show_result(self, output: str) -> None:
        """Display task result output."""
        print("\n--- Result ---")
        print(output)
        print("--- End ---\n")

    def show_cost_table(self, stats: Dict[str, Any], days: int) -> None:
        """Display cost statistics table."""
        print(f"\nToken Usage Summary (Last {days} Days)")
        print("-" * 45)
        print(f"{'Provider':<12} | {'Tokens':<10} | {'Cost'}")
        print("-" * 45)
        for provider, data in sorted(stats.get("by_provider", {}).items()):
            print(f"{provider:<12} | {data.get('tokens', 0):<10,} | ${data.get('cost', 0.0):.2f}")
        print("-" * 45)
        print(f"{'Total':<12} | {'':<10} | ${stats.get('total_cost', 0.0):.2f}")
        print()
