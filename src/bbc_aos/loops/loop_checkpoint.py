from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class LoopCheckpoint:
    """
    State checkpoint representing a specific iteration snapshot.
    Supports identifiers and metadata required for deterministic replay.
    """
    checkpoint_id: str
    trace_id: str
    replay_id: str
    deterministic_hash: str
    iteration_id: str
    parent_checkpoint_id: Optional[str] = None
    state_data: Dict[str, Any] = field(default_factory=dict)
    workspace_diff: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the checkpoint to a dictionary format."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "deterministic_hash": self.deterministic_hash,
            "iteration_id": self.iteration_id,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "state_data": self.state_data,
            "workspace_diff": self.workspace_diff,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopCheckpoint":
        """Deserializes a dictionary into a LoopCheckpoint object."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            trace_id=data["trace_id"],
            replay_id=data["replay_id"],
            deterministic_hash=data["deterministic_hash"],
            iteration_id=data["iteration_id"],
            parent_checkpoint_id=data.get("parent_checkpoint_id"),
            state_data=data.get("state_data", {}),
            workspace_diff=data.get("workspace_diff", {}),
        )
