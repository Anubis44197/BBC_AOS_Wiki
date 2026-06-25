"""Audit and observability summaries for BBC-AOS."""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


class LoopAudit:
    """Aggregates execution, commit, and failure memory data."""

    def __init__(self, project_root: str = ".") -> None:
        self.root = Path(project_root)

    def summary(self) -> Dict[str, Any]:
        events = self._load_jsonl(self.root / ".bbc" / "logs" / "commit_audit.jsonl")
        failures = self._load_jsonl(self.root / ".bbc" / "failure_memory.jsonl")
        executions = len(events)
        rollback_count = len([e for e in events if str(e.get("status", "")).upper() == "ROLLED_BACK"])
        file_counts: Counter[str] = Counter()
        for event in events:
            for file_path in event.get("affected_files", []):
                file_counts[str(file_path)] += 1
        common_failure = Counter(f.get("failure_type", "UNKNOWN") for f in failures).most_common(1)
        rejection_count = len([f for f in failures if f.get("failure_type") in ("VERIFICATION_REJECTION", "APPROVAL_TIMEOUT")])
        success_rate = 100 if executions and not failures else (0 if not executions else round((executions / (executions + len(failures))) * 100))
        return {
            "executions": executions,
            "success_rate": success_rate,
            "failures_pct": 100 - success_rate if executions or failures else 0,
            "rollback_count": rollback_count,
            "most_modified_file": file_counts.most_common(1)[0][0] if file_counts else "N/A",
            "most_common_failure": common_failure[0][0] if common_failure else "N/A",
            "average_latency_ms": 0,
            "human_rejection_rate": round((rejection_count / max(executions + len(failures), 1)) * 100),
        }

    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        return rows
