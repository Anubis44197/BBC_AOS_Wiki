from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class MemoryRecord:
    """
    Immutable representation of a single database record within the Memory Layer.
    Cannot be modified after creation. New updates generate a new record.
    """
    memory_id: str
    trace_id: str
    replay_id: str
    deterministic_hash: str
    version: int
    created_at: str
    originating_agent: str
    data: Dict[str, Any] = field(default_factory=dict)
