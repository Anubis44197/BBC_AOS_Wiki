from typing import Optional, Callable
from bbc_aos.memory.runtime.memory_record import MemoryRecord
from bbc_aos.memory.runtime.memory_exceptions import MemoryPromotionException

class MemoryPromotionManager:
    """
    Coordinates promotions of memory records across storage layers.
    Transitions: Working -> Episodic, Episodic -> Experience, Human -> Semantic.
    """
    def __init__(self) -> None:
        self.approval_provider: Optional[Callable[[MemoryRecord], bool]] = None

    def set_approval_provider(self, provider: Callable[[MemoryRecord], bool]) -> None:
        """Sets the callback to request human approval gates."""
        self.approval_provider = provider

    def promote(self, record: MemoryRecord, target_layer: str) -> MemoryRecord:
        """
        Validates and promotes a record to a target memory layer.
        
        Args:
            record: The source record to promote.
            target_layer: Key of target layer.
            
        Returns:
            MemoryRecord: Newly promoted record with incremented version.
            
        Raises:
            MemoryPromotionException: If transition path is invalid or approval fails.
        """
        source_layer = record.data.get("layer", "unknown")
        
        # 1. Verify valid promotion paths
        if source_layer == "working" and target_layer == "episodic":
            # Promotion path Working -> Episodic (Automatic)
            pass
        elif source_layer == "episodic" and target_layer == "experience":
            # Promotion path Episodic -> Experience (Automatic)
            pass
        elif source_layer == "human_knowledge" and target_layer == "semantic":
            # Promotion path Human -> Semantic (Requires explicit Approval)
            if not self.approval_provider or not self.approval_provider(record):
                raise MemoryPromotionException("Human -> Semantic promotion failed: human approval required")
        else:
            raise MemoryPromotionException(f"Unsupported promotion path: {source_layer} -> {target_layer}")

        # 2. Return new version of the record
        new_data = record.data.copy()
        new_data["layer"] = target_layer
        
        return MemoryRecord(
            memory_id=record.memory_id,
            trace_id=record.trace_id,
            replay_id=record.replay_id,
            deterministic_hash=record.deterministic_hash,
            version=record.version + 1,
            created_at=record.created_at,
            originating_agent=record.originating_agent,
            data=new_data
        )
