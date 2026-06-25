import time
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass(frozen=True)
class ObsidianAuditEvent:
    """
    Immutable event representing a transaction or action in the human knowledge layer.
    """
    event_id: str
    event_type: str
    trace_id: str
    replay_id: str
    deterministic_hash: str
    note_version: int
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


class ObsidianAuditLog:
    """
    Strictly append-only audit logger for tracking note synchronization events and lifecycle changes.
    """
    def __init__(self) -> None:
        self._events: List[ObsidianAuditEvent] = []

    def append(self, event: ObsidianAuditEvent) -> None:
        """
        Appends an event to the audit log.
        
        Args:
            event: The immutable audit event.
        """
        self._events.append(event)

    def get_events(self) -> List[ObsidianAuditEvent]:
        """
        Returns a shallow copy of the events list.
        """
        return list(self._events)
