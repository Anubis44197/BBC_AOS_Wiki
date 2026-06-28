"""Operational rollout modes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from bbc_aos.operations.loop_exceptions import InvalidLoopModeError
from bbc_aos.runtime_paths import loop_dir


class LoopMode(str, Enum):
    """BBC-AOS operational rollout levels."""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


MODE_LABELS = {
    LoopMode.L1: "OBSERVE",
    LoopMode.L2: "ASSIST",
    LoopMode.L3: "AUTONOMOUS",
}


@dataclass(frozen=True)
class LoopModeRecord:
    """Persisted loop mode metadata."""

    mode: LoopMode
    label: str
    read_only: bool
    approvals_required: bool
    commits_allowed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "label": self.label,
            "read_only": self.read_only,
            "approvals_required": self.approvals_required,
            "commits_allowed": self.commits_allowed,
        }


class LoopModeStore:
    """File-backed deterministic mode storage."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.path = loop_dir(self.project_root) / "mode.json"

    def get(self) -> LoopModeRecord:
        if not self.path.exists():
            return self._record(LoopMode.L2)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return self._record(LoopMode.L2)
        raw_mode = str(data.get("mode", "L2"))
        return self._record(parse_mode(raw_mode))

    def set(self, mode: LoopMode | str) -> LoopModeRecord:
        record = self._record(parse_mode(mode))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return record

    @staticmethod
    def _record(mode: LoopMode) -> LoopModeRecord:
        if mode == LoopMode.L1:
            return LoopModeRecord(mode, MODE_LABELS[mode], True, False, False)
        if mode == LoopMode.L2:
            return LoopModeRecord(mode, MODE_LABELS[mode], False, True, True)
        return LoopModeRecord(mode, MODE_LABELS[mode], False, True, True)


def parse_mode(mode: LoopMode | str) -> LoopMode:
    """Parse a mode string deterministically."""

    if isinstance(mode, LoopMode):
        return mode
    normalized = mode.strip().upper()
    if normalized in {"L1", "OBSERVE"}:
        return LoopMode.L1
    if normalized in {"L2", "ASSIST"}:
        return LoopMode.L2
    if normalized in {"L3", "AUTONOMOUS"}:
        return LoopMode.L3
    raise InvalidLoopModeError(f"Unknown loop mode: {mode}")
