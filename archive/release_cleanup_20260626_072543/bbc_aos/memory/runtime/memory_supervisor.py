import logging
from typing import Dict, List, Any
from bbc_aos.memory.runtime.memory_record import MemoryRecord
from bbc_aos.memory.runtime.memory_exceptions import MemoryConflictException
from bbc_aos.memory.runtime.memory_lifecycle_manager import MemoryLifecycleManager
from bbc_aos.memory.runtime.memory_audit_log import MemoryAuditLog

logger = logging.getLogger("bbc_aos.memory.runtime.memory_supervisor")

class MemorySupervisor:
    """
    Supervisor coordinating retention limits, lifecycle changes, promotions,
    conflict detection, and audit entries generation.
    """
    def __init__(self, audit_log: MemoryAuditLog) -> None:
        self.audit_log: MemoryAuditLog = audit_log
        self.lifecycle_manager: MemoryLifecycleManager = MemoryLifecycleManager()
        
        # Max record counts for retention enforcement
        self.retention_limits: Dict[str, int] = {
            "working": 50,
            "episodic": 500,
            "semantic": 10000,
            "human_knowledge": 10000,
            "experience": 1000,
        }

    def enforce_retention(self, layer: str, current_records: List[MemoryRecord]) -> List[MemoryRecord]:
        """
        Enforces retention constraints on a layer, archiving older records if limits are exceeded.
        
        Returns:
            List[MemoryRecord]: Detached list of archived records.
        """
        limit = self.retention_limits.get(layer, 1000)
        archived = []
        
        if len(current_records) > limit:
            overflow = len(current_records) - limit
            logger.warning(f"[RETENTION] Layer '{layer}' overflow detected. Archiving {overflow} records.")
            for i in range(overflow):
                rec = current_records[i]
                self.lifecycle_manager.transition_to(
                    rec.memory_id,
                    MemoryLifecycleManager.ARCHIVED,
                    reason="Retention limit exceeded"
                )
                archived.append(rec)
                self.generate_audit_event("ARCHIVE", rec)
        return archived

    def detect_conflicts(self, record: MemoryRecord, existing_records: List[MemoryRecord]) -> None:
        """
        Scans existing records for data hash or version collisions.
        
        Raises:
            MemoryConflictException: If version collision occurs or index hash differs for same ID.
        """
        for existing in existing_records:
            if existing.memory_id == record.memory_id:
                if existing.version == record.version:
                    raise MemoryConflictException(
                        f"Version collision: Record '{record.memory_id}' with version {record.version} already exists"
                    )
                # Verify that new versions do not have duplicate hashes
                if existing.deterministic_hash == record.deterministic_hash:
                    raise MemoryConflictException(
                        f"Deterministic hash collision: Hash '{record.deterministic_hash}' matches existing record"
                    )

    def validate_promotion(self, record: MemoryRecord, target_layer: str) -> None:
        """Validates that the source record exists in ACTIVE state before promotion."""
        current_state = self.lifecycle_manager.get_state(record.memory_id)
        if current_state != MemoryLifecycleManager.ACTIVE:
            raise MemoryLifecycleException(
                f"Cannot promote record '{record.memory_id}': state must be ACTIVE, got {current_state}"
            )

    def generate_audit_event(self, operation: str, record: MemoryRecord) -> str:
        """Generates an immutable audit trail entry for a memory operation."""
        layer = record.data.get("layer", "unknown")
        return self.audit_log.log_event(
            operation=operation,
            layer=layer,
            memory_id=record.memory_id,
            trace_id=record.trace_id,
            replay_id=record.replay_id,
            deterministic_hash=record.deterministic_hash
        )
