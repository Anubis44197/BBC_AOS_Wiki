from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class IntegrationResult:
    """
    Immutable representation of the outcome of a cross-subsystem integration operation.
    """
    success: bool
    trace_id: str
    replay_id: str
    deterministic_hash: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
