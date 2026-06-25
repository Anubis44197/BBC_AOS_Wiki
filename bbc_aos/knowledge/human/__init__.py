"""
Human Knowledge Layer and Obsidian integration package.
Exposes the core runtime components and gateway.
"""

from bbc_aos.knowledge.human.obsidian_exceptions import (
    ObsidianException,
    ObsidianFrozenRegistryException,
    ObsidianNoteLifecycleException,
    ObsidianSyncException,
    ObsidianSandboxViolationException,
)
from bbc_aos.knowledge.human.obsidian_registry import ObsidianRegistry
from bbc_aos.knowledge.human.note_record import NoteRecord, NoteLifecycleState
from bbc_aos.knowledge.human.proposal_artifact import ProposalArtifact
from bbc_aos.knowledge.human.sync_result import SyncResult
from bbc_aos.knowledge.human.sync_policy import SyncPolicy, SyncMode
from bbc_aos.knowledge.human.obsidian_audit_log import ObsidianAuditLog, ObsidianAuditEvent
from bbc_aos.knowledge.human.vault_indexer import VaultIndexer
from bbc_aos.knowledge.human.note_parser import NoteParser
from bbc_aos.knowledge.human.sync_planner import SyncPlanner
from bbc_aos.knowledge.human.promotion_reviewer import PromotionReviewer
from bbc_aos.knowledge.human.sync_supervisor import SyncSupervisor
from bbc_aos.knowledge.human.obsidian_gateway import ObsidianGateway

__all__ = [
    "ObsidianException",
    "ObsidianFrozenRegistryException",
    "ObsidianNoteLifecycleException",
    "ObsidianSyncException",
    "ObsidianSandboxViolationException",
    "ObsidianRegistry",
    "NoteRecord",
    "NoteLifecycleState",
    "ProposalArtifact",
    "SyncResult",
    "SyncPolicy",
    "SyncMode",
    "ObsidianAuditLog",
    "ObsidianAuditEvent",
    "VaultIndexer",
    "NoteParser",
    "SyncPlanner",
    "PromotionReviewer",
    "SyncSupervisor",
    "ObsidianGateway",
]
