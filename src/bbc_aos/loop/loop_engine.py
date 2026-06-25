"""Interactive BBC-AOS daemon loop engine."""

from typing import Any, Callable, Dict, Optional

from bbc_aos.loop.checkpoint_manager import CheckpointManager
from bbc_aos.loop.recovery_engine import RecoveryEngine
from bbc_aos.loop.retry_engine import RetryEngine
from bbc_aos.loop.state_machine import LoopState, LoopStateMachine


class LoopEngine:
    """Runs bounded BBC-AOS daemon iterations without default auto-commit."""

    MAX_ITERATIONS = 3
    HEAL_BUDGET = 3

    def __init__(
        self,
        project_root: str = ".",
        runner: Optional[Callable[[str], Dict[str, Any]]] = None,
    ) -> None:
        self.project_root = project_root
        self.runner = runner
        self.state_machine = LoopStateMachine()
        self.checkpoints = CheckpointManager(project_root)
        self.recovery = RecoveryEngine(self.checkpoints, self.HEAL_BUDGET)
        self.retry = RetryEngine(delays=(0.0, 0.0, 0.0))

    def run(
        self,
        goal: str,
        interactive: bool = True,
        max_iter: int = MAX_ITERATIONS,
        auto_approve: bool = False,
    ) -> Dict[str, Any]:
        max_iter = min(max_iter, self.MAX_ITERATIONS)
        summaries = []
        for iteration in range(1, max_iter + 1):
            self.state_machine.transition(LoopState.RUNNING)
            checkpoint = self.checkpoints.create(
                {
                    "goal": goal,
                    "iteration": iteration,
                    "state": self.state_machine.state.value,
                    "auto_approve": bool(auto_approve),
                    "interactive": bool(interactive),
                }
            )
            try:
                result = self.retry.run(lambda: self._run_once(goal))
                risk = result.get("risk_level", "LOW")
                self.state_machine.transition(LoopState.VERIFYING)
                if result.get("verdict") == "REJECTED":
                    self.state_machine.transition(LoopState.REJECTED)
                    summaries.append(result)
                    break
                if interactive or risk in ("MEDIUM", "HIGH", "CRITICAL") or not auto_approve:
                    result["awaiting_user_approval"] = True
                    summaries.append(result)
                    self.state_machine.transition(LoopState.IDLE)
                    break
                self.state_machine.transition(LoopState.COMMITTED)
                summaries.append(result)
                self.state_machine.transition(LoopState.IDLE)
            except Exception as exc:
                self.state_machine.transition(LoopState.FAILED)
                recovery = self.recovery.recover_latest()
                if recovery.get("status") == "FAILED_FINAL":
                    self.state_machine.transition(LoopState.FAILED_FINAL)
                else:
                    self.state_machine.transition(LoopState.RECOVERING)
                    self.state_machine.transition(LoopState.IDLE)
                return {
                    "status": self.state_machine.state.value,
                    "error": str(exc),
                    "recovery": recovery,
                    "checkpoint": checkpoint,
                }
        return {
            "status": self.state_machine.state.value,
            "iterations": len(summaries),
            "results": summaries,
        }

    def _run_once(self, goal: str) -> Dict[str, Any]:
        if self.runner:
            return self.runner(goal)
        return {
            "goal": goal,
            "status": "PLANNED",
            "verdict": "APPROVED",
            "risk_level": "LOW",
            "message": "Daemon runner not connected to ask pipeline yet.",
        }
