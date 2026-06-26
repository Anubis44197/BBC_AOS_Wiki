# Agent Roles Matrix - Phase 7A

This document defines the responsibilities, input and output contracts, goals, and scopes of the initial 7 agents of the BBC-AOS Agent Layer.

## 1. Summary Matrix Table

| Agent | Core Goal | Primary Input | Primary Output | Validation Dependency |
| :--- | :--- | :--- | :--- | :--- |
| **PlannerAgent** | Task decomposition & execution plans | Raw user request, system guidelines | Step-by-step task checklist | Rules schema verification |
| **ContextAgent** | Context retrieval & symbol lookup | Symbol query, project paths | Code fragments, imports metadata | SimHash index validation |
| **ResolverAgent** | Dependency analysis & blast-radius checks | Selected symbols, call graph | Impact score and dependency list | Symbol graph integrity |
| **CompressionAgent** | Context optimization & semantic packing | Raw compiled context payload | Compressed, packed context | Token count limits, AST match |
| **VerificationAgent** | Hallucination detection & contract check | Generated patch, target code | Security verdict (Pass/Fail) | CVP constraint engine |
| **DocumentationAgent** | Obsidian sync & knowledge note generation | Code modifications, task summary | Markdown pages, Obsidian backlinks | Markdown schema matching |
| **ExecutionAgent** | Controlled patches & file updates | Verified AST, code instructions | File diff, patch output | Syntax validator, Git tracker |

---

## 2. Agent Contract Details

### A. PlannerAgent
* **Goal:** Deconstruct complex tasks into actionable checklists.
* **Input Schema:** `{ "task_description": str, "rules": list }`
* **Output Schema:** `{ "steps": [{"step_id": str, "agent_type": str, "description": str}] }`
* **Safety Bounds:** Prevent loops or recursion in task planning. Maximum plan depth capped at 10.

### B. ContextAgent
* **Goal:** Locate code structures and retrieve prompt index contexts.
* **Input Schema:** `{ "symbols": [str], "project_path": str }`
* **Output Schema:** `{ "structures": [{"path": str, "code": str, "symbols_defined": [str]}] }`
* **Safety Bounds:** Sandbox paths. Access restricted to target project workspace; absolute external filesystem paths are blocked.

### C. ResolverAgent
* **Goal:** Estimate structural impact and trace dependency graphs.
* **Input Schema:** `{ "target_files": [str], "modified_symbols": [str] }`
* **Output Schema:** `{ "dependencies": [str], "blast_radius_score": float, "is_safe": bool }`
* **Safety Bounds:** Limits maximum depth traversal to 5 levels to avoid O(n^2) graph recursion overheads.

### D. CompressionAgent
* **Goal:** Strip non-essential code fragments and pack context segments.
* **Input Schema:** `{ "raw_context": dict, "target_tokens": int }`
* **Output Schema:** `{ "packed_context": str, "reduction_pct": float }`
* **Safety Bounds:** Ensure target preservation rules (e.g. keeping class definitions/signatures intact).

### E. VerificationAgent
* **Goal:** Guarantee that LLM patches do not reference fake symbols or violate code contracts.
* **Input Schema:** `{ "generated_code": str, "allowed_symbols": [str] }`
* **Output Schema:** `{ "verdict": str, "unknown_symbols": [str], "chaos_level": float }`
* **Safety Bounds:** Verdict must be binary (`PASS` or `FAIL`). If `unknown_symbols` count > 0, verdict is forced to `FAIL`.

### F. DocumentationAgent
* **Goal:** Update development wikis and build link structures.
* **Input Schema:** `{ "modifications": list, "notes": str }`
* **Output Schema:** `{ "notes_generated": [{"file_path": str, "markdown": str}] }`
* **Safety Bounds:** Rejects formatting containing HTML structures to preserve Obsidian backlink syntax constraints.

### G. ExecutionAgent
* **Goal:** Safely apply verified edits to source files.
* **Input Schema:** `{ "target_file": str, "patch": str }`
* **Output Schema:** `{ "file_written": bool, "diff": str }`
* **Safety Bounds:** Requires Git checkout status verification before write operations. All modifications are logged to transaction stores.
