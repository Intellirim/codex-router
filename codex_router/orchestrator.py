"""Parallel agent session management and coordination."""

from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from codex_router.config import Config
from codex_router.router import TaskRouter
from codex_router.tracker import CostTracker
from codex_router.display import Display


class Orchestrator:
    """Manages parallel execution of multiple AI agents."""

    def __init__(self, config: Config, tracker: CostTracker):
        """Initialize orchestrator."""
        self.config = config
        self.tracker = tracker
        self.router = TaskRouter(config)
        self.display = Display()

    def split_task(self, task: str, num_agents: int) -> List[str]:
        """Split task into subtasks for parallel execution.

        Args:
            task: Original task description
            num_agents: Number of parallel agents

        Returns:
            List of subtask descriptions
        """
        if num_agents == 1:
            return [task]

        subtasks = []
        for i in range(num_agents):
            subtasks.append(f"{task} (part {i + 1}/{num_agents})")

        return subtasks

    def run_parallel(self, task: str, num_agents: int, force_model: Optional[str] = None, budget: Optional[float] = None) -> Dict[str, Any]:
        """Execute task with multiple parallel agents."""
        if num_agents < 1:
            raise ValueError("Number of agents must be at least 1")
        if num_agents > 10:
            raise ValueError("Maximum 10 parallel agents supported")
        per_agent_budget = budget / num_agents if budget else None
        subtasks = self.split_task(task, num_agents)
        total_tokens = 0
        total_cost = 0.0
        outputs = []
        with ThreadPoolExecutor(max_workers=num_agents) as executor:
            futures = {}
            for idx, subtask in enumerate(subtasks):
                agent_id = idx + 1
                model = self.router.select_model(subtask, force_model)
                futures[executor.submit(self._execute_agent, agent_id, subtask, model, per_agent_budget)] = (agent_id, model)
            for future in as_completed(futures):
                agent_id, model = futures[future]
                try:
                    result = future.result()
                    outputs.append(result["output"])
                    total_tokens += result["tokens"]
                    total_cost += result["cost"]
                    self.tracker.record_usage(model, result["tokens"], result["cost"])
                    self.display.agent_complete(agent_id, result["tokens"], result["cost"])
                except Exception as e:
                    self.display.error(f"Agent-{agent_id} failed: {str(e)}")
                    raise ValueError(f"Agent {agent_id} execution failed")
        if budget and total_cost > budget:
            raise ValueError(f"Total cost ${total_cost:.3f} exceeded budget ${budget:.2f}")
        return {"outputs": outputs, "total_tokens": total_tokens, "total_cost": total_cost}

    def _execute_agent(self, agent_id: int, task: str, model: str, budget: Optional[float]) -> Dict[str, Any]:
        """Execute single agent task."""
        self.display.agent_start(agent_id, model)
        result = self.router.execute_task(task, model, budget)
        return {"output": result["output"], "tokens": result["tokens"], "cost": result["cost"]}
