from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class LoopContext:
    """
    Immutable context model containing parameters and identifiers for a loop execution session.
    Cannot be modified after instantiation.
    """
    trace_id: str
    replay_id: str
    task_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
