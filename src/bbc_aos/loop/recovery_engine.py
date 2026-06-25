"""Recovery helper for BBC-AOS daemon loop."""

from typing import Any, Dict

from bbc_aos.loop.checkpoint_manager import CheckpointManager


class RecoveryEngine:
    """Restores the latest checkpoint until the heal budget is exhausted."""

    def __init__(self, checkpoint_manager: CheckpointManager, heal_budget: int = 3) -> None:
        self.checkpoint_manager = checkpoint_manager
        self.heal_budget = heal_budget

    def recover_latest(self) -> Dict[str, Any]:
        if self.heal_budget <= 0:
            return {"status": "FAILED_FINAL", "reason": "heal budget exhausted"}
        self.heal_budget -= 1
        snapshot = self.checkpoint_manager.latest()
        return {
            "status": "RECOVERED",
            "remaining_heal_budget": self.heal_budget,
            "checkpoint": snapshot,
        }
