from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from bbc_aos.memory.runtime.memory_record import MemoryRecord

@dataclass
class MemoryResult:
    """
    Response payload returned by executing a query filter on the Memory Layer.
    """
    records: List[MemoryRecord] = field(default_factory=list)
    audit_hash: str = "none"
    metadata: Dict[str, Any] = field(default_factory=dict)
