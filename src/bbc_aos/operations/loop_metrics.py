"""Operational loop metrics."""

from __future__ import annotations

from typing import Any

from bbc_aos.operations.loop_budget import LoopBudget
from bbc_aos.operations.loop_mode import LoopModeRecord


def compute_metrics(budget: LoopBudget, mode: LoopModeRecord) -> dict[str, Any]:
    """Compute deterministic operational metrics."""

    executions = budget.executions
    failures = budget.failures
    success_count = max(0, executions - failures)
    success_rate = int((success_count / executions) * 100) if executions else 100
    failure_rate = int((failures / executions) * 100) if executions else 0
    average_runtime = int(budget.runtime_ms / executions) if executions else 0
    return {
        "executions": executions,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "failures": failures,
        "rollbacks": budget.rollbacks,
        "average_runtime_ms": average_runtime,
        "current_mode": mode.mode.value,
    }
