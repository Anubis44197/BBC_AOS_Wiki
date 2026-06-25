from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class LoopResult:
    """
    Structured outcome contract returned at the conclusion of a loop run.
    Contains mandatory tracing ids, timing parameters, and final termination states.
    """
    trace_id: str
    replay_id: str
    deterministic_hash: str
    checkpoint_id: Optional[str]
    execution_time_ms: float
    final_state: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the result to a dictionary format."""
        return {
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "deterministic_hash": self.deterministic_hash,
            "checkpoint_id": self.checkpoint_id,
            "execution_time_ms": self.execution_time_ms,
            "final_state": self.final_state,
            "success": self.success,
            "data": self.data,
            "error_details": self.error_details,
        }
