# Architecture Design

BBC-AOS is designed as a secure sidecar agentic pipeline wrapper. It separates execution concerns into sequential agent stages and transaction controllers.

## Stage Execution Workflow

```
Developer Prompt -> PlannerAgent -> ContextAgent -> CoderAgent -> TesterAgent -> VerificationAgent -> ApprovalManager -> CommitManager
```

1. **PlannerAgent**: Decomposes developer prompts into a deterministic, DAG-based task checklist.
2. **ContextAgent**: Queries the semantic memory layer via `MemoryManager`, compiles relevant files, and collapses them using `SemanticPacker` (path aliases, import deduplication).
3. **CoderAgent**: Translates compiled context and tasks into a unified diff patch (`CodeDiff`).
4. **TesterAgent**: Creates structured validation plans mapped to priorities.
5. **VerificationAgent**: Performs AST analyses on code imports, verifying blast-radius compliance and structural rules.
6. **ApprovalManager**: Evaluates risk policy rules:
   * **LOW**: Auto-approves.
   * **MEDIUM/HIGH**: Interactive approval requests.
   * **CRITICAL**: Triggers escalation hooks for manual review.
7. **CommitManager**: Verifies the approval token, creates file snapshots, applies patches inside the sandbox filesystem, and transactionally commits or rolls back on failures.
