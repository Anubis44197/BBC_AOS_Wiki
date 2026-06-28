"""Append-only operational loop run log."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from bbc_aos.runtime_paths import loop_dir


@dataclass(frozen=True)
class LoopRunRecord:
    """One operational loop run event."""

    trace_id: str
    replay_id: str
    loop_id: str
    mode: str
    goal: str
    start_time: str
    end_time: str
    status: str
    approval_id: str = ""
    commit_hash: str = ""
    failure_reason: str = ""


class LoopRunLog:
    """JSONL-backed immutable loop history."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.path = loop_dir(self.project_root) / "run_log.jsonl"

    def append(self, record: LoopRunRecord) -> LoopRunRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")
        return record

    def history(self, last: int = 20) -> list[LoopRunRecord]:
        if not self.path.exists():
            return []
        rows = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        selected = rows[-max(0, last) :] if last else rows
        records: list[LoopRunRecord] = []
        for row in selected:
            data = json.loads(row)
            if isinstance(data, dict):
                records.append(
                    LoopRunRecord(
                        trace_id=str(data.get("trace_id", "")),
                        replay_id=str(data.get("replay_id", "")),
                        loop_id=str(data.get("loop_id", "")),
                        mode=str(data.get("mode", "")),
                        goal=str(data.get("goal", "")),
                        start_time=str(data.get("start_time", "")),
                        end_time=str(data.get("end_time", "")),
                        status=str(data.get("status", "")),
                        approval_id=str(data.get("approval_id", "")),
                        commit_hash=str(data.get("commit_hash", "")),
                        failure_reason=str(data.get("failure_reason", "")),
                    )
                )
        return records
