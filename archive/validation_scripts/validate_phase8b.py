import os
import sys
import unittest
from typing import Dict, Any

# Ensure project path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.knowledge.human import (
    ObsidianException,
    ObsidianFrozenRegistryException,
    ObsidianNoteLifecycleException,
    ObsidianSyncException,
    ObsidianSandboxViolationException,
    ObsidianRegistry,
    NoteRecord,
    NoteLifecycleState,
    ProposalArtifact,
    SyncResult,
    SyncPolicy,
    SyncMode,
    ObsidianAuditLog,
    ObsidianAuditEvent,
    VaultIndexer,
    NoteParser,
    SyncPlanner,
    PromotionReviewer,
    SyncSupervisor,
    ObsidianGateway,
)


class TestObsidianRuntimeSkeleton(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ObsidianRegistry()
        self.registry.reset()
        self.audit_log = ObsidianAuditLog()
        self.gateway = ObsidianGateway(self.registry, self.audit_log)

    def test_syntax_and_imports(self) -> None:
        """1. Validate syntax and imports of all Obsidian runtime classes."""
        self.assertIsNotNone(ObsidianException)
        self.assertIsNotNone(ObsidianFrozenRegistryException)
        self.assertIsNotNone(ObsidianNoteLifecycleException)
        self.assertIsNotNone(ObsidianSyncException)
        self.assertIsNotNone(ObsidianSandboxViolationException)
        self.assertIsNotNone(ObsidianRegistry)
        self.assertIsNotNone(NoteRecord)
        self.assertIsNotNone(NoteLifecycleState)
        self.assertIsNotNone(ProposalArtifact)
        self.assertIsNotNone(SyncResult)
        self.assertIsNotNone(SyncPolicy)
        self.assertIsNotNone(SyncMode)
        self.assertIsNotNone(ObsidianAuditLog)
        self.assertIsNotNone(ObsidianAuditEvent)
        self.assertIsNotNone(VaultIndexer)
        self.assertIsNotNone(NoteParser)
        self.assertIsNotNone(SyncPlanner)
        self.assertIsNotNone(PromotionReviewer)
        self.assertIsNotNone(SyncSupervisor)
        self.assertIsNotNone(ObsidianGateway)

    def test_record_immutability(self) -> None:
        """2. Validate NoteRecord, ProposalArtifact, and SyncResult are strictly immutable."""
        note = NoteRecord(
            note_id="note_1",
            note_type="Decision",
            version=1,
            created_at="2026-06-24T18:30:00Z",
            updated_at="2026-06-24T18:30:00Z",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            originating_agent="agent_1",
            title="Design Decision",
            content="Use Python 3.10",
            state=NoteLifecycleState.DRAFT,
        )
        self.assertEqual(note.note_id, "note_1")
        with self.assertRaises(AttributeError):
            note.version = 2  # type: ignore

        proposal = ProposalArtifact(
            proposal_id="prop_1",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            rationale="Update design",
            safety_assessment={"risk": "low"},
            originating_agent="agent_1",
            proposed_note=note,
        )
        self.assertEqual(proposal.proposal_id, "prop_1")
        with self.assertRaises(AttributeError):
            proposal.rationale = "New rationale"  # type: ignore

    def test_registry_uniqueness_and_freeze(self) -> None:
        """3. Validate vault registry uniqueness validations and freeze gate constraints."""
        self.assertFalse(self.registry.is_frozen)
        
        self.registry.register_vault("vault_core", "/path/to/core")
        self.assertEqual(self.registry.get_vault_path("vault_core"), "/path/to/core")

        # Uniqueness verification
        with self.assertRaises(ValueError):
            self.registry.register_vault("vault_core", "/another/path")

        # Freeze locking verification
        self.registry.freeze()
        self.assertTrue(self.registry.is_frozen)

        with self.assertRaises(ObsidianFrozenRegistryException):
            self.registry.register_vault("vault_extra", "/path/to/extra")

    def test_lifecycle_validation(self) -> None:
        """4. Verify note lifecycle states exist and match specification."""
        self.assertEqual(NoteLifecycleState.DRAFT, "DRAFT")
        self.assertEqual(NoteLifecycleState.PROPOSED, "PROPOSED")
        self.assertEqual(NoteLifecycleState.REVIEW_PENDING, "REVIEW_PENDING")
        self.assertEqual(NoteLifecycleState.APPROVED, "APPROVED")
        self.assertEqual(NoteLifecycleState.REJECTED, "REJECTED")
        self.assertEqual(NoteLifecycleState.ARCHIVED, "ARCHIVED")

    def test_proposal_validation(self) -> None:
        """5. Validate ProposalArtifact data contracts and SyncSupervisor validation."""
        note = NoteRecord(
            note_id="note_1",
            note_type="Decision",
            version=1,
            created_at="2026-06-24T18:30:00Z",
            updated_at="2026-06-24T18:30:00Z",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            originating_agent="agent_1",
            title="Design Decision",
            content="Use Python 3.10",
            state=NoteLifecycleState.DRAFT,
        )

        valid_proposal = ProposalArtifact(
            proposal_id="prop_1",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            rationale="Update design",
            safety_assessment={"risk": "low"},
            originating_agent="agent_1",
            proposed_note=note,
        )

        # SyncSupervisor validation checks
        supervisor = self.gateway.supervisor
        self.assertTrue(supervisor.validate_proposal(valid_proposal))

        invalid_proposal = ProposalArtifact(
            proposal_id="",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="",
            rationale="Update design",
            safety_assessment={},
            originating_agent="",
            proposed_note=note,
        )
        self.assertFalse(supervisor.validate_proposal(invalid_proposal))

    def test_supervised_sync_and_approval(self) -> None:
        """6. Validate sync execution constraints (manual approval requirement, automatic merge prohibition)."""
        note = NoteRecord(
            note_id="note_1",
            note_type="Decision",
            version=1,
            created_at="2026-06-24T18:30:00Z",
            updated_at="2026-06-24T18:30:00Z",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            originating_agent="agent_1",
            title="Design Decision",
            content="Use Python 3.10",
            state=NoteLifecycleState.DRAFT,
        )

        proposal = ProposalArtifact(
            proposal_id="prop_1",
            trace_id="t_1",
            replay_id="r_1",
            deterministic_hash="hash_1",
            rationale="Update design",
            safety_assessment={"risk": "low"},
            originating_agent="agent_1",
            proposed_note=note,
        )

        policy = SyncPolicy(mode=SyncMode.APPROVAL_REQUIRED_MERGE)

        # Sync without approval must succeed but not merge/commit the notes
        res_unapproved = self.gateway.sync([proposal], approved=False, policy=policy)
        self.assertFalse(res_unapproved.success)
        self.assertEqual(len(res_unapproved.synced_notes), 0)

        # Sync with approval commits note and generates append-only audit event
        res_approved = self.gateway.sync([proposal], approved=True, policy=policy)
        self.assertTrue(res_approved.success)
        self.assertEqual(len(res_approved.synced_notes), 1)
        self.assertEqual(res_approved.synced_notes[0], "note_1")

        # Confirm audit event was recorded with all required fields
        events = self.audit_log.get_events()
        self.assertEqual(len(events), 1)
        evt = events[0]
        self.assertEqual(evt.trace_id, "t_1")
        self.assertEqual(evt.replay_id, "r_1")
        self.assertEqual(evt.deterministic_hash, "hash_1")
        self.assertEqual(evt.note_version, 1)

        # Confirm automatic merge mode is blocked
        invalid_policy = SyncPolicy(mode=SyncMode.APPROVAL_REQUIRED_MERGE, allow_automatic_merge=True)
        with self.assertRaises(ObsidianSyncException):
            self.gateway.sync([proposal], approved=True, policy=invalid_policy)

    def test_observability_hooks_and_replay(self) -> None:
        """7. Verify observability hooks and replay validation contracts."""
        hooks_triggered = []

        def hook_cb(*args, **kwargs):
            hooks_triggered.append(True)

        self.gateway.supervisor.register_hook("before_sync", hook_cb)
        self.gateway.supervisor.register_hook("after_sync", hook_cb)

        note = NoteRecord(
            note_id="note_1",
            note_type="Decision",
            version=1,
            created_at="2026-06-24T18:30:00Z",
            updated_at="2026-06-24T18:30:00Z",
            trace_id="t_obs",
            replay_id="r_obs",
            deterministic_hash="hash_obs",
            originating_agent="agent_1",
            title="Design Decision",
            content="Use Python 3.10",
            state=NoteLifecycleState.DRAFT,
        )

        proposal = ProposalArtifact(
            proposal_id="prop_obs",
            trace_id="t_obs",
            replay_id="r_obs",
            deterministic_hash="hash_obs",
            rationale="Update design",
            safety_assessment={"risk": "low"},
            originating_agent="agent_1",
            proposed_note=note,
        )

        policy = SyncPolicy(mode=SyncMode.APPROVAL_REQUIRED_MERGE)
        self.gateway.sync([proposal], approved=True, policy=policy)

        # Check hooks fired
        self.assertEqual(len(hooks_triggered), 2)

        # Replay event lookup by replay_id
        replay_events = self.gateway.replay_transactions("r_obs")
        self.assertEqual(len(replay_events), 1)
        self.assertEqual(replay_events[0].trace_id, "t_obs")


if __name__ == "__main__":
    unittest.main()
