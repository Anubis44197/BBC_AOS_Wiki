from typing import Dict, Any

class MemoryQuery:
    """
    Defines filters, paging, and sorting parameters for querying memory records.
    """
    def __init__(
        self,
        layer: str,
        filters: Dict[str, Any] = None,
        max_results: int = 10,
        deterministic_sort: str = "created_at_asc"
    ) -> None:
        self.layer: str = layer
        self.filters: Dict[str, Any] = filters or {}
        self.max_results: int = max_results
        self.deterministic_sort: str = deterministic_sort
