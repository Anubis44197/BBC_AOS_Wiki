"""Checkpoint persistence for BBC-AOS daemon iterations."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List


class CheckpointManager:
    """Stores iteration snapshots under `.bbc/state`."""

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / ".bbc" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        checkpoint_id = payload.get("checkpoint_id") or f"cp_{int(time.time() * 1000)}"
        snapshot = dict(payload)
        snapshot["checkpoint_id"] = checkpoint_id
        snapshot["created_at"] = snapshot.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%S")
        path = self.state_dir / f"{checkpoint_id}.json"
        path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        return snapshot

    def restore(self, checkpoint_id: str) -> Dict[str, Any]:
        path = self.state_dir / f"{checkpoint_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def latest(self) -> Dict[str, Any]:
        checkpoints: List[Path] = sorted(self.state_dir.glob("cp_*.json"), key=lambda p: p.stat().st_mtime)
        if not checkpoints:
            raise FileNotFoundError("No checkpoints available")
        return json.loads(checkpoints[-1].read_text(encoding="utf-8"))
