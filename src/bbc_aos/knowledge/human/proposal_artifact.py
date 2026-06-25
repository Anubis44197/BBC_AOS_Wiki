from dataclasses import dataclass, field
from typing import Dict, Any
from bbc_aos.knowledge.human.note_record import NoteRecord

@dataclass(frozen=True)
class ProposalArtifact:
    """
    Immutable representation of a change proposal artifact submitted for human review.
    """
    proposal_id: str
    trace_id: str
    replay_id: str
    deterministic_hash: str
    rationale: str
    safety_assessment: Dict[str, Any]
    originating_agent: str
    proposed_note: NoteRecord
    metadata: Dict[str, Any] = field(default_factory=dict)
