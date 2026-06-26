from typing import List
from bbc_aos.knowledge.human.note_record import NoteRecord
from bbc_aos.knowledge.human.proposal_artifact import ProposalArtifact
from bbc_aos.knowledge.human.sync_policy import SyncPolicy

class SyncPlanner:
    """
    Computes local-to-remote changes and packages modifications as ProposalArtifacts.
    """
    def generate_proposals(
        self,
        local_notes: List[NoteRecord],
        remote_notes: List[NoteRecord],
        policy: SyncPolicy,
    ) -> List[ProposalArtifact]:
        """
        Creates a list of sync proposals between the local and remote sets.
        
        Args:
            local_notes: Notes indexed from the local workspace vault.
            remote_notes: Remote note snapshots.
            policy: The synchronization policy.
            
        Returns:
            List of generated ProposalArtifacts.
        """
        return []
