import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List

@dataclass(frozen=True)
class IntegrationAuditEvent:
    """
    Immutable representation of an audit event representing a subsystem interaction.
    """
    event_id: str
    event_type: str
    trace_id: str
    replay_id: str
    deterministic_hash: str
    agent_name: str = "system"
    status: str = "UNKNOWN"
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "deterministic_hash": self.deterministic_hash,
            "agent_name": self.agent_name,
            "status": self.status,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationAuditEvent":
        return cls(
            event_id=str(data["event_id"]),
            event_type=str(data["event_type"]),
            trace_id=str(data["trace_id"]),
            replay_id=str(data["replay_id"]),
            deterministic_hash=str(data["deterministic_hash"]),
            agent_name=str(data.get("agent_name", "system")),
            status=str(data.get("status", "UNKNOWN")),
            timestamp=float(data.get("timestamp", time.time())),
            details=dict(data.get("details", {})),
        )


class IntegrationAuditLog:
    """
    Strictly append-only audit logger for tracing system-wide integration dispatches.
    """
    def __init__(self, project_root: str | Path = ".", load_existing: bool = False) -> None:
        self.project_root = Path(project_root)
        self.audit_path = self.project_root / ".bbc" / "logs" / "integration_audit.jsonl"
        self.log_path = self.audit_path
        self._events: List[IntegrationAuditEvent] = []
        if load_existing:
            self._load_existing()

    def append(self, event: IntegrationAuditEvent) -> None:
        """
        Appends an event to the integration audit log.
        
        Args:
            event: The immutable audit event.
        """
        self._events.append(event)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as audit_file:
            audit_file.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    def append_event(
        self,
        event_type: str,
        trace_id: str,
        replay_id: str,
        agent_name: str,
        status: str,
        details: Dict[str, Any] | None = None,
    ) -> IntegrationAuditEvent:
        payload = {
            "event_type": event_type,
            "trace_id": trace_id,
            "replay_id": replay_id,
            "agent_name": agent_name,
            "status": status,
            "details": details or {},
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        deterministic_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        event_id = hashlib.sha256(f"{time.time()}:{serialized}".encode("utf-8")).hexdigest()
        event = IntegrationAuditEvent(
            event_id=event_id,
            event_type=event_type,
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
            agent_name=agent_name,
            status=status,
            details=details or {},
        )
        self.append(event)
        return event

    def get_events(self) -> List[IntegrationAuditEvent]:
        """Returns a shallow copy of the events list."""
        return list(self._events)

    def _load_existing(self) -> None:
        if not self.audit_path.exists():
            return
        for line in self.audit_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                self._events.append(IntegrationAuditEvent.from_dict(json.loads(line)))
            except Exception:
                continue
