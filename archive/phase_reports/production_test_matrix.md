# Production Test Matrix - Phase 10A

This document details the test matrix, inputs, objectives, and assertions required for final production certification.

## 1. Test Execution Matrix

| Domain | Test ID | Verification Objective | Input Parameters | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Determinism** | `DET-01` | Shannon chaos density consistency | 100-run multi-dataset inputs | Zero drift (variance = 0) |
| **Determinism** | `DET-02` | Matrix condition number stability | Near-singular matrices | Dynamic pivot healing, stable outputs |
| **Replay** | `REP-01` | Core equations replay equivalence | Trace parameters JSON | Hash match to original calculation |
| **Replay** | `REP-02` | E2E rehydration and re-execution | Historical `replay_id` logs | Reconstructed state matches log target |
| **Integration** | `INT-01` | Direct communication blocking | Attempt Agent -> Memory bypass | Raised `IntegrationValidationException` |
| **Integration** | `INT-02` | Subsystem health sweeps check | Registry check mock statuses | Reports Status: OK/UNHEALTHY |
| **Recovery** | `REC-01` | Retry recovery state rehydration | Exhaust loop budget | Halted loop, rolled back to checkpoint |
| **Recovery** | `REC-02` | Escalation alert dispatch | Fail checkpoint recovery | Trigger `on_health_degraded` hook |
| **Memory** | `MEM-01` | Record immutability freeze | Modify `MemoryRecord` attributes | Raised `AttributeError` |
| **Memory** | `MEM-02` | Promotion approval checking | Promote Human -> Semantic | Checked callback status, block if None |
| **Knowledge** | `KNO-01` | Local note isolation constraints | Attempt direct user note modification | Rejection of edits, proposal-only generation |
| **Knowledge** | `KNO-02` | Automatic merge blocks | Force automatic merge policy | Raised `ObsidianSyncException` |
| **Security** | `SEC-01` | Directory sandbox isolation | Attempt write to `C:/Windows/` | Raised `ObsidianSandboxViolationException` |
| **Production** | `PROD-01` | Deterministic startup ordering | Startup step sequence | Ordered audit logs matches expectation |
| **Production** | `PROD-02` | Graceful shutdown sequence | Trigger system shutdown | Active loops drain, memory flushed |
