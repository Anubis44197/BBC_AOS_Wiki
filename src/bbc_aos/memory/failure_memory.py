"""Persistent recurring failure memory for BBC-AOS."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List


class FailureMemory:
    """Append-only JSONL failure memory with occurrence counters."""

    def __init__(self, project_root: str = ".") -> None:
        self.path = Path(project_root) / ".bbc" / "failure_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record_failure(
        self,
        trace_id: str,
        failure_type: str,
        root_cause: str,
        affected_files: Iterable[str] = (),
        resolution: str = "",
    ) -> Dict[str, Any]:
        records = self.list_failures()
        fingerprint = self._fingerprint(failure_type, root_cause, affected_files)
        existing = next((r for r in records if r.get("failure_id") == fingerprint), None)
        if existing:
            existing["occurrence_count"] = int(existing.get("occurrence_count", 1)) + 1
            existing["trace_id"] = trace_id
            existing["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            existing["resolution"] = resolution or existing.get("resolution", "")
            self._rewrite(records)
            return existing

        record = {
            "failure_id": fingerprint,
            "trace_id": trace_id,
            "failure_type": failure_type,
            "root_cause": root_cause,
            "affected_files": sorted(set(str(f) for f in affected_files)),
            "resolution": resolution,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "occurrence_count": 1,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def list_failures(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        records: List[Dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            r for r in self.list_failures()
            if q in json.dumps(r, sort_keys=True).lower()
        ]

    def _rewrite(self, records: List[Dict[str, Any]]) -> None:
        self.path.write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
            encoding="utf-8",
        )

    def _fingerprint(
        self,
        failure_type: str,
        root_cause: str,
        affected_files: Iterable[str],
    ) -> str:
        payload = {
            "failure_type": failure_type,
            "root_cause": root_cause,
            "affected_files": sorted(set(str(f) for f in affected_files)),
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return f"fail_{digest[:16]}"
