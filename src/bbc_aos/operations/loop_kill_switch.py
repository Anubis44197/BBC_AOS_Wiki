"""Operational kill switch."""

from __future__ import annotations

from pathlib import Path


class LoopKillSwitch:
    """File-backed hard stop signal."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.path = self.project_root / ".bbc" / "loop" / "KILL_SWITCH"

    def activate(self, reason: str = "manual") -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(f"active=true\nreason={reason}\n", encoding="utf-8")
        return self.path

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def active(self) -> bool:
        return self.path.exists()
