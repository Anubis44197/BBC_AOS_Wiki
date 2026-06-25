from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any

class NoteLifecycleState(str, Enum):
    """
    Standard lifecycle states for local-first user notes and change proposals.
    """
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    REVIEW_PENDING = "REVIEW_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class NoteRecord:
    """
    Immutable representation of a human knowledge note in the local-first vault.
    """
    note_id: str
    note_type: str
    version: int
    created_at: str
    updated_at: str
    trace_id: str
    replay_id: str
    deterministic_hash: str
    originating_agent: str
    title: str
    content: str
    state: NoteLifecycleState
    metadata: Dict[str, Any] = field(default_factory=dict)
