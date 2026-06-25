import time
from dataclasses import dataclass, field
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
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


class IntegrationAuditLog:
    """
    Strictly append-only audit logger for tracing system-wide integration dispatches.
    """
    def __init__(self) -> None:
        self._events: List[IntegrationAuditEvent] = []

    def append(self, event: IntegrationAuditEvent) -> None:
        """
        Appends an event to the integration audit log.
        
        Args:
            event: The immutable audit event.
        """
        self._events.append(event)

    def get_events(self) -> List[IntegrationAuditEvent]:
        """Returns a shallow copy of the events list."""
        return list(self._events)
