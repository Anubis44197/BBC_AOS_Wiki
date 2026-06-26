"""Operational loop scheduler contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoopScheduleDecision:
    """Deterministic scheduler decision."""

    should_run: bool
    reason: str


class LoopScheduler:
    """Small deterministic scheduler facade for future daemon integration."""

    def decide(self, kill_switch_active: bool, paused: bool) -> LoopScheduleDecision:
        if kill_switch_active:
            return LoopScheduleDecision(False, "kill_switch_active")
        if paused:
            return LoopScheduleDecision(False, "loop_paused")
        return LoopScheduleDecision(True, "ready")
