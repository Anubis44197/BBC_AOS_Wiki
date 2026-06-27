"""High-level Operational Loop Layer manager."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from bbc_aos.operations.loop_budget import LoopBudgetStore, budget_summary
from bbc_aos.operations.loop_kill_switch import LoopKillSwitch
from bbc_aos.operations.loop_metrics import compute_metrics
from bbc_aos.operations.loop_mode import LoopModeStore
from bbc_aos.operations.loop_pattern_registry import LoopPatternRegistry
from bbc_aos.operations.loop_readiness import LoopReadinessAuditor
from bbc_aos.operations.loop_registry import LoopRegistry, RegisteredLoop
from bbc_aos.operations.loop_run_log import LoopRunLog, LoopRunRecord
from bbc_aos.operations.loop_state import LoopStateRecord, LoopStateStore, OperationalLoopState
from bbc_aos.wiki.paths import resolve_workspace_vault


class LoopManager:
    """Facade for BBC-AOS operational loop commands."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.mode_store = LoopModeStore(self.project_root)
        self.state_store = LoopStateStore(self.project_root)
        self.budget_store = LoopBudgetStore(self.project_root)
        self.pattern_registry = LoopPatternRegistry(self.project_root)
        self.run_log = LoopRunLog(self.project_root)
        self.kill_switch = LoopKillSwitch(self.project_root)
        self.registry = LoopRegistry(self.project_root)

    def init(self) -> dict[str, str]:
        loop_dir = self.project_root / ".bbc" / "loop"
        loop_dir.mkdir(parents=True, exist_ok=True)
        self.mode_store.set("L2")
        self.state_store.save(LoopStateRecord())
        self.budget_store.save(self.budget_store.load())
        self.pattern_registry.write_default_yaml()
        self.export_state()
        return {"loop_dir": str(loop_dir), "mode": "L2"}

    def set_mode(self, mode: str) -> dict[str, object]:
        record = self.mode_store.set(mode)
        state = self.state_store.load()
        state.mode = record.mode.value
        self.state_store.save(state)
        self.export_state()
        return record.to_dict()

    def status(self) -> dict[str, Any]:
        state = self.state_store.load()
        return state.to_dict()

    def pause(self) -> dict[str, Any]:
        return self._set_state(OperationalLoopState.PAUSED)

    def resume(self) -> dict[str, Any]:
        return self._set_state(OperationalLoopState.RUNNING)

    def stop(self) -> dict[str, Any]:
        return self._set_state(OperationalLoopState.STOPPED)

    def kill(self, reason: str = "manual") -> dict[str, str]:
        self.kill_switch.activate(reason)
        state = self.state_store.load()
        state.status = OperationalLoopState.STOPPED.value
        state.failure_reason = f"kill_switch:{reason}"
        self.state_store.save(state)
        self.log_run(goal="kill", status="STOPPED", failure_reason=state.failure_reason)
        self.export_state()
        return {"status": "STOPPED", "kill_switch": str(self.kill_switch.path)}

    def audit(self) -> dict[str, Any]:
        return LoopReadinessAuditor(self.project_root).audit()

    def patterns(self) -> list[dict[str, object]]:
        return [pattern.to_dict() for pattern in self.pattern_registry.all()]

    def describe(self, pattern_name: str) -> dict[str, object]:
        return self.pattern_registry.get(pattern_name).to_dict()

    def start(self, pattern_name: str, goal: str = "") -> dict[str, Any]:
        if self.kill_switch.active():
            state = self.state_store.load()
            state.status = OperationalLoopState.STOPPED.value
            state.failure_reason = f"kill_switch:{self.kill_switch.reason() or 'active'}"
            self.state_store.save(state)
            self.log_run(goal=goal or pattern_name, status="BLOCKED", failure_reason=state.failure_reason)
            self.export_state()
            raise RuntimeError("Loop start blocked: kill switch is active")
        pattern = self.pattern_registry.get(pattern_name)
        loop_id = f"{pattern.name}_loop"
        self.budget_store.enforce()
        state = self.state_store.load()
        state.loop_id = loop_id
        state.status = OperationalLoopState.WAITING_APPROVAL.value if pattern.human_gate == "required" else OperationalLoopState.RUNNING.value
        state.mode = pattern.mode
        state.current_goal = goal or pattern.description
        self.state_store.save(state)
        self.registry.register(RegisteredLoop(loop_id, pattern.name, pattern.mode, state.status))
        self.log_run(goal=state.current_goal, status=state.status, loop_id=loop_id, mode=pattern.mode)
        self.budget_store.record_execution(runtime_ms=0, shadow=True)
        self.export_state()
        return state.to_dict()

    def budget(self) -> dict[str, Any]:
        return budget_summary(self.budget_store.load())

    def metrics(self) -> dict[str, Any]:
        return compute_metrics(self.budget_store.load(), self.mode_store.get())

    def history(self, last: int = 20) -> list[dict[str, str]]:
        return [record.__dict__ for record in self.run_log.history(last)]

    def log_run(
        self,
        goal: str,
        status: str,
        loop_id: str = "default",
        mode: str = "",
        failure_reason: str = "",
    ) -> LoopRunRecord:
        stable = f"{loop_id}:{goal}:{status}:{failure_reason}"
        digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]
        record = LoopRunRecord(
            trace_id=f"tr_{digest}",
            replay_id=f"rp_{digest}",
            loop_id=loop_id,
            mode=mode or self.mode_store.get().mode.value,
            goal=goal,
            start_time="deterministic",
            end_time="deterministic",
            status=status,
            failure_reason=failure_reason,
        )
        return self.run_log.append(record)

    def export_state(self) -> Path:
        state = self.state_store.load()
        vault_path = resolve_workspace_vault(self.project_root) / "Loop"
        vault_path.mkdir(parents=True, exist_ok=True)
        output = vault_path / "STATE.md"
        body = (
            "# BBC-AOS Loop State\n\n"
            f"Current Goal:\n{state.current_goal or 'None'}\n\n"
            f"Status:\n{state.status}\n\n"
            f"Mode:\n{state.mode}\n\n"
            f"Last Execution:\n{state.last_execution or 'None'}\n\n"
            f"Failure:\n{state.failure_reason or 'None'}\n\n"
            "Next Action:\n"
            f"{_next_action(state.status)}\n\n"
            "Last Updated:\ndeterministic\n"
        )
        output.write_text(body, encoding="utf-8")
        return output

    def _set_state(self, target: OperationalLoopState) -> dict[str, Any]:
        current = self.state_store.load()
        try:
            state = self.state_store.transition(target)
        except Exception:
            current.status = target.value
            state = self.state_store.save(current)
        self.export_state()
        return state.to_dict()


def _next_action(status: str) -> str:
    if status == OperationalLoopState.WAITING_APPROVAL.value:
        return "Human review required"
    if status == OperationalLoopState.FAILED.value:
        return "Review failure and recover"
    if status == OperationalLoopState.PAUSED.value:
        return "Resume or stop loop"
    if status == OperationalLoopState.STOPPED.value:
        return "Clear stop condition before restart"
    return "Continue normal operation"
