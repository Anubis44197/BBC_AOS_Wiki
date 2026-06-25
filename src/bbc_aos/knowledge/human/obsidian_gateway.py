from typing import List, Optional, Callable, Dict, Any
from bbc_aos.knowledge.human.obsidian_registry import ObsidianRegistry
from bbc_aos.knowledge.human.note_record import NoteRecord
from bbc_aos.knowledge.human.proposal_artifact import ProposalArtifact
from bbc_aos.knowledge.human.sync_result import SyncResult
from bbc_aos.knowledge.human.sync_policy import SyncPolicy
from bbc_aos.knowledge.human.sync_supervisor import SyncSupervisor
from bbc_aos.knowledge.human.obsidian_audit_log import ObsidianAuditLog, ObsidianAuditEvent
from bbc_aos.knowledge.human.vault_indexer import VaultIndexer
from bbc_aos.knowledge.human.note_parser import NoteParser
from bbc_aos.knowledge.human.sync_planner import SyncPlanner
from bbc_aos.knowledge.human.promotion_reviewer import PromotionReviewer

class ObsidianGateway:
    """
    The sole entrypoint for the Obsidian/Human Knowledge subsystem.
    Coordinating indexing, parsing, planning, reviewing, audit logging,
    and supervised synchronization.
    """
    def __init__(self, registry: ObsidianRegistry, audit_log: Optional[ObsidianAuditLog] = None) -> None:
        self.registry = registry
        self.audit_log = audit_log or ObsidianAuditLog()
        self.supervisor = SyncSupervisor(self.audit_log)
        self.indexer = VaultIndexer()
        self.parser = NoteParser()
        self.planner = SyncPlanner()
        self.reviewer = PromotionReviewer()

    def index_vault(self, vault_name: str) -> List[NoteRecord]:
        """
        Indexes all notes in a registered vault.
        
        Args:
            vault_name: Name of the registered vault.
        """
        self.supervisor.trigger_hook("before_read", vault_name)
        path = self.registry.get_vault_path(vault_name)
        records = self.indexer.index_vault(path)
        self.supervisor.trigger_hook("after_read", records)
        return records

    def propose_changes(
        self,
        local_notes: List[NoteRecord],
        remote_notes: List[NoteRecord],
        policy: SyncPolicy,
    ) -> List[ProposalArtifact]:
        """
        Plans synchronization and generates change proposals.
        
        Args:
            local_notes: Notes from local vault.
            remote_notes: Notes from remote/shared vault.
            policy: Sync policy.
        """
        self.supervisor.trigger_hook("before_propose", local_notes, remote_notes)
        proposals = self.planner.generate_proposals(local_notes, remote_notes, policy)
        self.supervisor.trigger_hook("after_propose", proposals)
        return proposals

    def sync(self, proposals: List[ProposalArtifact], approved: bool, policy: SyncPolicy) -> SyncResult:
        """
        Executes synchronization under supervision (approval required).
        
        Args:
            proposals: List of ProposalArtifacts.
            approved: Whether user has approved the sync.
            policy: SyncPolicy.
        """
        return self.supervisor.execute_sync(proposals, approved, policy)

    def review_promotion(self, note: NoteRecord, callback: Callable[[NoteRecord], bool]) -> bool:
        """
        Reviews promotion of a human note to semantic memory.
        
        Args:
            note: NoteRecord targeted for promotion.
            callback: Explicit human approval callback.
        """
        reviewer = PromotionReviewer(callback)
        return reviewer.review_promotion(note)

    def get_audit_log(self) -> ObsidianAuditLog:
        """Retrieves the append-only audit log."""
        return self.audit_log

    def replay_transactions(self, replay_id: str) -> List[ObsidianAuditEvent]:
        """
        Replays historical sync events for deterministic validation.
        
        Args:
            replay_id: Unique replay transaction ID.
        """
        return self.supervisor.generate_replay(replay_id)
