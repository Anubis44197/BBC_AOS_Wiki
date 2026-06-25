from typing import List, Callable, Dict, Any
from bbc_aos.knowledge.human.note_record import NoteRecord
from bbc_aos.knowledge.human.proposal_artifact import ProposalArtifact
from bbc_aos.knowledge.human.sync_result import SyncResult
from bbc_aos.knowledge.human.sync_policy import SyncPolicy
from bbc_aos.knowledge.human.obsidian_audit_log import ObsidianAuditLog, ObsidianAuditEvent
from bbc_aos.knowledge.human.obsidian_exceptions import ObsidianSyncException

class SyncSupervisor:
    """
    Supervises synchronization operations, validates proposals, enforces approvals,
    runs merge validation, generates audits, and manages observability hooks.
    """
    def __init__(self, audit_log: ObsidianAuditLog) -> None:
        self.audit_log = audit_log
        self._hooks: Dict[str, List[Callable[..., Any]]] = {
            "before_read": [],
            "after_read": [],
            "before_propose": [],
            "after_propose": [],
            "before_sync": [],
            "after_sync": [],
            "on_approval_required": [],
            "on_replay": []
        }

    def register_hook(self, name: str, callback: Callable[..., Any]) -> None:
        """Registers a callback hook."""
        if name in self._hooks:
            self._hooks[name].append(callback)

    def trigger_hook(self, name: str, *args, **kwargs) -> None:
        """Triggers all callbacks registered under the hook name."""
        if name in self._hooks:
            for callback in self._hooks[name]:
                callback(*args, **kwargs)

    def validate_proposal(self, proposal: ProposalArtifact) -> bool:
        """
        Validates the proposal structure and safety constraints.
        
        Args:
            proposal: The proposal artifact to validate.
        """
        if not proposal.proposal_id or not proposal.trace_id or not proposal.replay_id or not proposal.deterministic_hash:
            return False
        if not proposal.proposed_note:
            return False
        return True

    def validate_merge(self, base: NoteRecord, incoming: NoteRecord) -> bool:
        """
        Validates that merge does not violate any safety rules (no automatic merges).
        
        Args:
            base: Existing note record.
            incoming: Proposed note record.
        """
        # Automatic merges are strictly forbidden. Any merge requires explicit manual approval.
        return False

    def enforce_approval(self, proposal: ProposalArtifact, approved: bool) -> bool:
        """
        Enforces manual human approval before synchronization.
        
        Args:
            proposal: The proposal artifact.
            approved: True if approved by the user, False otherwise.
        """
        if not approved:
            self.trigger_hook("on_approval_required", proposal)
            return False
        return True

    def execute_sync(self, proposals: List[ProposalArtifact], approved: bool, policy: SyncPolicy) -> SyncResult:
        """
        Executes supervised synchronization of note proposals.
        
        Args:
            proposals: List of ProposalArtifacts.
            approved: Status of human approval.
            policy: SyncPolicy configuration.
            
        Raises:
            ObsidianSyncException: If validation fails or automatic merge is requested.
        """
        self.trigger_hook("before_sync", proposals, policy)
        
        # Verify no automatic merge is allowed
        if policy.allow_automatic_merge:
            raise ObsidianSyncException("Automatic merges are strictly forbidden")

        synced_notes = []
        audit_event_ids = []

        for prop in proposals:
            if not self.validate_proposal(prop):
                raise ObsidianSyncException(f"Invalid proposal artifact: {prop.proposal_id}")
            
            # Enforce manual approval
            if not self.enforce_approval(prop, approved):
                continue
                
            # Create audit event
            event = ObsidianAuditEvent(
                event_id=f"evt_{prop.proposal_id}",
                event_type="sync_commit",
                trace_id=prop.trace_id,
                replay_id=prop.replay_id,
                deterministic_hash=prop.deterministic_hash,
                note_version=prop.proposed_note.version,
                details={"proposal_id": prop.proposal_id, "note_id": prop.proposed_note.note_id}
            )
            self.audit_log.append(event)
            audit_event_ids.append(event.event_id)
            synced_notes.append(prop.proposed_note.note_id)

        result = SyncResult(
            success=len(synced_notes) > 0,
            trace_id=proposals[0].trace_id if proposals else "none",
            replay_id=proposals[0].replay_id if proposals else "none",
            deterministic_hash=proposals[0].deterministic_hash if proposals else "none",
            synced_notes=synced_notes,
            audit_event_ids=audit_event_ids
        )
        self.trigger_hook("after_sync", result)
        return result

    def generate_replay(self, replay_id: str) -> List[ObsidianAuditEvent]:
        """
        Generates audit history for a specific replay transaction.
        
        Args:
            replay_id: Unique replay transaction ID.
        """
        self.trigger_hook("on_replay", replay_id)
        return [evt for evt in self.audit_log.get_events() if evt.replay_id == replay_id]
