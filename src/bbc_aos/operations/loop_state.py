"""Operational loop state management."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any

from bbc_aos.operations.loop_exceptions import InvalidLoopStateError
from bbc_aos.operations.loop_mode import LoopMode


class OperationalLoopState(str, Enum):
    """Supported operational loop states."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"


STATE_TRANSITIONS: dict[OperationalLoopState, set[OperationalLoopState]] = {
    OperationalLoopState.IDLE: {OperationalLoopState.RUNNING, OperationalLoopState.PAUSED},
    OperationalLoopState.RUNNING: {
        OperationalLoopState.WAITING_APPROVAL,
        OperationalLoopState.FAILED,
        OperationalLoopState.PAUSED,
        OperationalLoopState.STOPPED,
        OperationalLoopState.COMPLETED,
    },
    OperationalLoopState.WAITING_APPROVAL: {
        OperationalLoopState.RUNNING,
        OperationalLoopState.PAUSED,
        OperationalLoopState.STOPPED,
        OperationalLoopState.COMPLETED,
    },
    OperationalLoopState.FAILED: {
        OperationalLoopState.RECOVERING,
        OperationalLoopState.PAUSED,
        OperationalLoopState.STOPPED,
    },
    OperationalLoopState.RECOVERING: {
        OperationalLoopState.RUNNING,
        OperationalLoopState.FAILED,
        OperationalLoopState.STOPPED,
    },
    OperationalLoopState.PAUSED: {OperationalLoopState.RUNNING, OperationalLoopState.STOPPED},
    OperationalLoopState.STOPPED: {OperationalLoopState.IDLE},
    OperationalLoopState.COMPLETED: {OperationalLoopState.IDLE},
}


@dataclass
class LoopStateRecord:
    """Persisted operational loop state."""

    loop_id: str = "default"
    status: str = OperationalLoopState.IDLE.value
    mode: str = LoopMode.L2.value
    current_goal: str = ""
    started_at: str = ""
    last_execution: str = ""
    last_success: str = ""
    last_failure: str = ""
    failure_reason: str = ""
    next_execution: str = ""
    retry_count: int = 0
    budget_usage: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["budget_usage"] = self.budget_usage or {}
        return data


class LoopStateStore:
    """File-backed deterministic state store."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.path = self.project_root / ".bbc" / "loop" / "STATE.json"

    def load(self) -> LoopStateRecord:
        if not self.path.exists():
            return LoopStateRecord()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return LoopStateRecord()
        return LoopStateRecord(
            loop_id=str(data.get("loop_id", "default")),
            status=str(data.get("status", OperationalLoopState.IDLE.value)),
            mode=str(data.get("mode", LoopMode.L2.value)),
            current_goal=str(data.get("current_goal", "")),
            started_at=str(data.get("started_at", "")),
            last_execution=str(data.get("last_execution", "")),
            last_success=str(data.get("last_success", "")),
            last_failure=str(data.get("last_failure", "")),
            failure_reason=str(data.get("failure_reason", "")),
            next_execution=str(data.get("next_execution", "")),
            retry_count=int(data.get("retry_count", 0)),
            budget_usage=_coerce_int_dict(data.get("budget_usage", {})),
        )

    def save(self, record: LoopStateRecord) -> LoopStateRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(record.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return record

    def transition(self, target: OperationalLoopState | str) -> LoopStateRecord:
        record = self.load()
        current = OperationalLoopState(record.status)
        next_state = OperationalLoopState(target)
        if next_state not in STATE_TRANSITIONS[current]:
            raise InvalidLoopStateError(f"Invalid loop transition: {current.value} -> {next_state.value}")
        record.status = next_state.value
        return self.save(record)


def _coerce_int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        if isinstance(key, str) and isinstance(raw, int):
            result[key] = raw
    return result
