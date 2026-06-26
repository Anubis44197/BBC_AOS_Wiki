"""Operational loop registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class RegisteredLoop:
    """Registered operational loop metadata."""

    loop_id: str
    pattern: str
    mode: str
    status: str


class LoopRegistry:
    """File-backed registered-loop index."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.path = Path(project_root) / ".bbc" / "loop" / "registry.json"

    def list(self) -> list[RegisteredLoop]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        loops: list[RegisteredLoop] = []
        for item in data:
            if isinstance(item, dict):
                loops.append(
                    RegisteredLoop(
                        loop_id=str(item.get("loop_id", "")),
                        pattern=str(item.get("pattern", "")),
                        mode=str(item.get("mode", "")),
                        status=str(item.get("status", "")),
                    )
                )
        return loops

    def register(self, loop: RegisteredLoop) -> RegisteredLoop:
        loops = [existing for existing in self.list() if existing.loop_id != loop.loop_id]
        loops.append(loop)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(item) for item in sorted(loops, key=lambda row: row.loop_id)], indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return loop
