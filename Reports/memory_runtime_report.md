# Memory Runtime Report - Phase 8A

This report details the package layout, component structures, and safety constraints implemented in the `bbc_aos` Memory Layer runtime skeletons.

## 1. Directory Structure Layout

The skeleton framework is implemented under the [`bbc_aos/memory/runtime/`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/memory/runtime/) package directory:

```
bbc_aos/memory/runtime/
├── __init__.py                # Package exports for all memory components
├── memory_exceptions.py       # Custom RPC-compatible exceptions
├── memory_registry.py         # Thread-safe layer registry with freeze lock
├── memory_record.py           # Immutable MemoryRecord structure
├── memory_query.py            # Search query parameter filters
├── memory_result.py           # Structured query outputs
├── memory_index.py            # Search indexing mappings
├── memory_audit_log.py        # Append-only transaction logger
├── memory_lifecycle_manager.py # State machine (CREATED, INDEXED, ACTIVE, etc.)
├── memory_visibility_policy.py# Visibility rules for agents, loops, and humans
├── memory_promotion_manager.py# Layer transitions (Working -> Episodic -> Experience)
├── memory_supervisor.py       # Audits, retention bounds, conflict resolver
└── memory_manager.py          # Sole orchestrator gateway with hooks
```

---

## 2. Memory Record Immutability and Append-Only Writes

* **Frozen Dataclass:** `MemoryRecord` is defined using Python's `@dataclass(frozen=True)`. Attempting to modify properties after creation raises `AttributeError`.
* **Append-Only Storage:** Once created, records are committed to the memory database list. Changes to a record require generating a new record instance with an incremented version number (`version = current_version + 1`), preserving the historical data intact.

---

## 3. Visibility and Promotion Policies

* **Read/Write Scopes:** The `MemoryVisibilityPolicy` separates permissions:
  * *Human Knowledge:* System cannot write directly (Human Role only).
  * *Semantic Memory:* Modified via human approval promotion gates only.
  * *Working/Episodic:* Writable by the loop execution engine.
* **Promotion Gates:** The `MemoryPromotionManager` implements the three allowed transition flows. Human -> Semantic promotions require an approval callback to block execution until explicit authorization is received.
