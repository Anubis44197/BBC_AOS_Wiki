from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any

class SyncMode(str, Enum):
    """
    Allowed modes of synchronization for local-first vaults.
    """
    PULL_ONLY = "pull-only"
    PROPOSAL_BASED_PUSH = "proposal-based push"
    APPROVAL_REQUIRED_MERGE = "approval-required merge"


@dataclass(frozen=True)
class SyncPolicy:
    """
    Policies governing sync validations, permissions, and gates.
    """
    mode: SyncMode
    allow_automatic_merge: bool = False  # Always False per architectural constraints
    require_human_approval: bool = True  # Always True per architectural constraints
    metadata: Dict[str, Any] = field(default_factory=dict)
