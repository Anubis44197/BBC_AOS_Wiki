from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class IntegrationContext:
    """
    Immutable representation of execution context scoping trace, replay, and deterministic hashes.
    """
    trace_id: str
    replay_id: str
    deterministic_hash: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
