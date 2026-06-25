# Agent Runtime Contracts Specification - Phase 7B

This document defines the class signatures, interface parameters, and payload schemas for all allowlisted agent actions in `bbc_aos`.

---

## 1. Abstract Message Contracts

All communications are bound to standard JSON-RPC 2.0 structures:

### A. Request Payload Standard
```json
{
  "jsonrpc": "2.0",
  "id": "<string_or_uuid>",
  "method": "<agent_id>.<action>",
  "params": {
    "task_id": "<uuid>",
    "context": {
      "project_path": "<string>",
      "target_file": "<string_optional>",
      "symbols": ["<list_optional>"]
    },
    "constraints": {},
    "metadata": {
      "originating_agent": "<string>",
      "trace_id": "<uuid>"
    }
  }
}
```

### B. Response Payload Standard (Success)
```json
{
  "jsonrpc": "2.0",
  "id": "<string_or_uuid>",
  "result": {
    "status": "success",
    "data": {}
  }
}
```

### C. Response Payload Standard (Error)
```json
{
  "jsonrpc": "2.0",
  "id": "<string_or_uuid>",
  "error": {
    "code": "<integer>",
    "message": "<string>",
    "data": {
      "traceback": "<string_optional>"
    }
  }
}
```

---

## 2. Agent Action Signatures

### A. PlannerAgent
* **Action:** `planner_agent.create_plan`
* **Input Schema:** `{ "context": { "task_description": str } }`
* **Output Schema:** `{ "steps": [{"step_id": str, "agent_type": str, "description": str}] }`

### B. ContextAgent
* **Action:** `context_agent.get_symbol_context`
* **Input Schema:** `{ "context": { "symbols": list } }`
* **Output Schema:** `{ "structures": [{"path": str, "symbols_defined": list, "code_content": str}] }`

### C. ResolverAgent
* **Action:** `resolver_agent.resolve_dependencies`
* **Input Schema:** `{ "context": { "target_files": list } }`
* **Output Schema:** `{ "dependencies": list, "blast_radius_score": float, "is_safe": bool }`

### D. CompressionAgent
* **Action:** `compression_agent.optimize_context`
* **Input Schema:** `{ "context": { "raw_context": dict } }`
* **Output Schema:** `{ "packed_context": str, "reduction_pct": float }`

### E. VerificationAgent
* **Action:** `verification_agent.check_hallucinations`
* **Input Schema:** `{ "context": { "generated_code": str } }`
* **Output Schema:** `{ "verdict": str, "unknown_symbols": list }`

### F. DocumentationAgent
* **Action:** `documentation_agent.generate_notes`
* **Input Schema:** `{ "context": { "modifications": list } }`
* **Output Schema:** `{ "notes_generated": [{"file_path": str, "markdown": str}] }`

### G. ExecutionAgent
* **Action:** `execution_agent.apply_patch`
* **Input Schema:** `{ "context": { "target_file": str, "patch": str } }`
* **Output Schema:** `{ "file_written": bool, "diff": str }`
