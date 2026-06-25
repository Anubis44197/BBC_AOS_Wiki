from typing import Dict, List, Any
from bbc_aos.memory.runtime.memory_record import MemoryRecord

class MemoryIndex:
    """
    Index map representing retrieval keys to memory records.
    Coordinates deterministic search indexing and unique lookups.
    """
    def __init__(self) -> None:
        self._index_map: Dict[str, List[MemoryRecord]] = {}

    def index_record(self, key: str, record: MemoryRecord) -> None:
        """
        Indexes a record under a queryable key string.
        
        Args:
            key: Lookup index string.
            record: Immutable memory record reference.
        """
        if key not in self._index_map:
            self._index_map[key] = []
        self._index_map[key].append(record)

    def lookup(self, key: str) -> List[MemoryRecord]:
        """Retrieves list of records matching key, or empty if not found."""
        return self._index_map.get(key, [])
