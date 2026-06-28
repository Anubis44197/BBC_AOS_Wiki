"""Operational loop budget engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from bbc_aos.operations.loop_exceptions import LoopBudgetExceededError
from bbc_aos.runtime_paths import loop_dir


@dataclass
class LoopBudget:
    """Hard loop limits and usage counters."""

    max_iterations: int = 3
    max_runtime_minutes: int = 30
    max_failures: int = 3
    max_daily_runs: int = 50
    executions: int = 0
    runtime_ms: int = 0
    estimated_tokens_saved: int = 0
    shadow_runs: int = 0
    approvals: int = 0
    failures: int = 0
    rollbacks: int = 0
    commits: int = 0

    def to_dict(self) -> dict[str, int]:
        return {key: int(value) for key, value in asdict(self).items()}


class LoopBudgetStore:
    """File-backed budget storage and limit enforcement."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.path = loop_dir(self.project_root) / "budget.json"

    def load(self) -> LoopBudget:
        if not self.path.exists():
            return LoopBudget()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return LoopBudget()
        values = {field: int(data.get(field, getattr(LoopBudget(), field))) for field in LoopBudget.__dataclass_fields__}
        return LoopBudget(**values)

    def save(self, budget: LoopBudget) -> LoopBudget:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(budget.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return budget

    def enforce(self, budget: LoopBudget | None = None) -> None:
        current = budget or self.load()
        if current.max_iterations > 3:
            raise LoopBudgetExceededError("max_iterations must remain <= 3 by default policy")
        if current.failures > current.max_failures:
            raise LoopBudgetExceededError("max_failures exceeded")
        if current.executions > current.max_daily_runs:
            raise LoopBudgetExceededError("max_daily_runs exceeded")

    def record_execution(
        self,
        runtime_ms: int = 0,
        tokens_saved: int = 0,
        shadow: bool = False,
        approved: bool = False,
        failed: bool = False,
        rollback: bool = False,
        committed: bool = False,
    ) -> LoopBudget:
        budget = self.load()
        budget.executions += 1
        budget.runtime_ms += max(0, runtime_ms)
        budget.estimated_tokens_saved += max(0, tokens_saved)
        budget.shadow_runs += int(shadow)
        budget.approvals += int(approved)
        budget.failures += int(failed)
        budget.rollbacks += int(rollback)
        budget.commits += int(committed)
        self.enforce(budget)
        return self.save(budget)


def budget_summary(budget: LoopBudget) -> dict[str, Any]:
    average_runtime = int(budget.runtime_ms / budget.executions) if budget.executions else 0
    return {
        **budget.to_dict(),
        "average_runtime_ms": average_runtime,
        "loop_cost": "$0 (local mode)",
    }
