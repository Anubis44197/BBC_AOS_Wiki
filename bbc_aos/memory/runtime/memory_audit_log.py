import logging
from typing import Dict, Any, List

logger = logging.getLogger("bbc_aos.memory.runtime.memory_audit_log")

class MemoryAuditLog:
    """
    Append-only transaction logger recording every memory read, write, or promotion.
    Audit log events are immutable.
    """
    def __init__(self) -> None:
        self._audit_records: List[Dict[str, Any]] = []

    def log_event(
        self,
        operation: str,
        layer: str,
        memory_id: str,
        trace_id: str,
        replay_id: str,
        deterministic_hash: str
    ) -> str:
        """
        Appends an immutable audit event for a memory operation.
        
        Returns:
            str: Generated audit event hash.
        """
        import hashlib
        
        # Calculate a unique audit event signature hash
        raw_sig = f"{operation}:{layer}:{memory_id}:{trace_id}:{replay_id}:{deterministic_hash}"
        event_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()

        event = {
            "operation": operation,
            "layer": layer,
            "memory_id": memory_id,
            "trace_id": trace_id,
            "replay_id": replay_id,
            "deterministic_hash": deterministic_hash,
            "event_hash": event_hash,
        }
        
        self._audit_records.append(event)
        logger.info(f"[AUDIT LOG] {operation} on layer '{layer}' (Memory ID: {memory_id}) | Hash: {event_hash}")
        
        return event_hash

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Returns read-only copy of the transaction logs."""
        return list(self._audit_records)
