"""Operational kill switch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bbc_aos.runtime_paths import loop_dir


class LoopKillSwitch:
    """File-backed hard stop signal."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        loop_root = loop_dir(self.project_root)
        self.path = loop_root / "kill_switch.json"
        self.legacy_path = loop_root / "KILL_SWITCH"

    def activate(self, reason: str = "manual") -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"active": True, "reason": reason}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        self.legacy_path.write_text(f"active=true\nreason={reason}\n", encoding="utf-8")
        return self.path

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
        if self.legacy_path.exists():
            self.legacy_path.unlink()

    def active(self) -> bool:
        if self.path.exists():
            try:
                data: Any = json.loads(self.path.read_text(encoding="utf-8"))
                return isinstance(data, dict) and bool(data.get("active"))
            except Exception:
                return True
        return self.legacy_path.exists()

    def reason(self) -> str:
        if not self.path.exists():
            return "legacy" if self.legacy_path.exists() else ""
        try:
            data: Any = json.loads(self.path.read_text(encoding="utf-8"))
            return str(data.get("reason", "")) if isinstance(data, dict) else ""
        except Exception:
            return "unreadable"
