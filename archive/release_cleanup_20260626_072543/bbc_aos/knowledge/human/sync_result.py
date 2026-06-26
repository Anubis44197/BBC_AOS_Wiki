from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass(frozen=True)
class SyncResult:
    """
    Immutable representation of the outcome of a synchronization session.
    """
    success: bool
    trace_id: str
    replay_id: str
    deterministic_hash: str
    synced_notes: List[str] = field(default_factory=list)
    audit_event_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
