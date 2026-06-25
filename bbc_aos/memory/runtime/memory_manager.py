import time
import logging
from typing import Dict, List, Any, Optional, Callable
from bbc_aos.memory.runtime.memory_record import MemoryRecord
from bbc_aos.memory.runtime.memory_query import MemoryQuery
from bbc_aos.memory.runtime.memory_result import MemoryResult
from bbc_aos.memory.runtime.memory_exceptions import (
    MemoryException,
    MemoryFrozenRegistryException,
    MemoryConflictException,
)
from bbc_aos.memory.runtime.memory_registry import MemoryRegistry
from bbc_aos.memory.runtime.memory_supervisor import MemorySupervisor
from bbc_aos.memory.runtime.memory_audit_log import MemoryAuditLog
from bbc_aos.memory.runtime.memory_visibility_policy import MemoryVisibilityPolicy
from bbc_aos.memory.runtime.memory_promotion_manager import MemoryPromotionManager
from bbc_aos.memory.runtime.memory_lifecycle_manager import MemoryLifecycleManager

logger = logging.getLogger("bbc_aos.memory.runtime.memory_manager")

class MemoryManager:
    """
    The only authorized runtime entrypoint for all bbc_aos Memory operations.
    Exposes records creation, querying, promotions, archiving, and audits.
    """
    def __init__(self) -> None:
        self.registry: MemoryRegistry = MemoryRegistry()
        self.audit_log: MemoryAuditLog = MemoryAuditLog()
        self.supervisor: MemorySupervisor = MemorySupervisor(self.audit_log)
        self.visibility_policy: MemoryVisibilityPolicy = MemoryVisibilityPolicy()
        self.promotion_manager: MemoryPromotionManager = MemoryPromotionManager()
        
        # Local append-only database simulator
        self._database: Dict[str, List[MemoryRecord]] = {
            "working": [],
            "episodic": [],
            "semantic": [],
            "human_knowledge": [],
            "experience": [],
        }

        # Observability hooks registry
        self.hooks: Dict[str, Callable[..., None]] = {
            "before_create": lambda record_params: None,
            "after_create": lambda record: None,
            "before_query": lambda query: None,
            "after_query": lambda result: None,
            "before_promote": lambda record, target: None,
            "after_promote": lambda record: None,
            "on_conflict": lambda record, err: None,
            "on_archive": lambda memory_id: None,
        }

    def create_record(self, record_params: Dict[str, Any], actor_role: str) -> MemoryRecord:
        """
        Creates and appends an immutable memory record to the database.
        """
        self.hooks["before_create"](record_params)
        
        layer = record_params.get("layer", "working")
        self.visibility_policy.check_write_permission(actor_role, layer)

        # Build immutable record
        record = MemoryRecord(
            memory_id=record_params["memory_id"],
            trace_id=record_params["trace_id"],
            replay_id=record_params["replay_id"],
            deterministic_hash=record_params["deterministic_hash"],
            version=record_params.get("version", 1),
            created_at=record_params.get("created_at", "2026-06-24T18:20:00Z"),
            originating_agent=record_params["originating_agent"],
            data=record_params.get("data", {})
        )

        # Conflict check
        existing = self._database.get(layer, [])
        try:
            self.supervisor.detect_conflicts(record, existing)
        except MemoryConflictException as e:
            self.hooks["on_conflict"](record, e)
            raise e

        # Append-only insert
        self._database[layer].append(record)
        
        # Transition lifecycle state: CREATED -> INDEXED -> ACTIVE
        self.supervisor.lifecycle_manager.transition_to(
            record.memory_id,
            MemoryLifecycleManager.INDEXED,
            reason="Record indexed"
        )
        self.supervisor.lifecycle_manager.transition_to(
            record.memory_id,
            MemoryLifecycleManager.ACTIVE,
            reason="Record activated"
        )
        
        # Audit entry
        self.supervisor.generate_audit_event("CREATE", record)
        
        # Retention check
        self.supervisor.enforce_retention(layer, self._database[layer])

        self.hooks["after_create"](record)
        return record

    def query(self, query: MemoryQuery, actor_role: str) -> MemoryResult:
        """Queries memory records in a layer, verifying visibility permissions."""
        self.hooks["before_query"](query)
        
        layer = query.layer
        self.visibility_policy.check_read_permission(actor_role, layer)

        records = self._database.get(layer, [])
        
        # Filtering simulation
        filtered = []
        for r in records:
            match = True
            for k, v in query.filters.items():
                if r.data.get(k) != v and getattr(r, k, None) != v:
                    match = False
                    break
            if match:
                filtered.append(r)

        # Sorting (Deterministic sort asc/desc)
        if query.deterministic_sort == "created_at_asc":
            filtered.sort(key=lambda x: x.created_at)

        # Truncate
        results = filtered[:query.max_results]

        # Audit lookup
        for r in results:
            self.supervisor.generate_audit_event("READ", r)

        res = MemoryResult(records=results)
        self.hooks["after_query"](res)
        return res

    def archive(self, memory_id: str, actor_role: str) -> None:
        """Transitions a record's lifecycle state to ARCHIVED."""
        self.hooks["on_archive"](memory_id)
        
        # Transition lifecycle
        self.supervisor.lifecycle_manager.transition_to(
            memory_id,
            MemoryLifecycleManager.ARCHIVED,
            reason=f"Archived by actor: {actor_role}"
        )

    def promote(self, record: MemoryRecord, target_layer: str, actor_role: str) -> MemoryRecord:
        """Promotes an active record across layers."""
        self.hooks["before_promote"](record, target_layer)
        
        # Validate that the source layer is readable and the target layer is writable
        source_layer = record.data.get("layer", "working")
        self.visibility_policy.check_read_permission(actor_role, source_layer)
        self.visibility_policy.check_write_permission(actor_role, target_layer)
        
        self.supervisor.validate_promotion(record, target_layer)

        # Promote record
        promoted = self.promotion_manager.promote(record, target_layer)
        
        # Add to database
        self._database[target_layer].append(promoted)
        
        # Transition lifecycle state
        if self.supervisor.lifecycle_manager.get_state(promoted.memory_id) != MemoryLifecycleManager.ACTIVE:
            self.supervisor.lifecycle_manager.transition_to(
                promoted.memory_id,
                MemoryLifecycleManager.ACTIVE,
                reason=f"Promoted to {target_layer}"
            )
        
        # Audit event
        self.supervisor.generate_audit_event("PROMOTE", promoted)

        self.hooks["after_promote"](promoted)
        return promoted

    def freeze(self) -> None:
        """Locks the memory registry and prevents modifications."""
        self.registry.freeze()
        logger.info("[MEMORY MANAGER] Subsystem registry is frozen")

    def audit(self) -> List[Dict[str, Any]]:
        """Exposes immutable audit logs."""
        return self.audit_log.history
