# Deployment Readiness Checklist - Phase 10A

This document outlines the acceptance criteria, rollback procedures, and the production deployment workflow.

## 1. Production Acceptance Criteria

Before any code deployment to production, the system must satisfy the following thresholds:

* **Fidelity Metric:** 100% equivalence match on all core core calculations.
* **Variance Metric:** Zero variance (variance = 0) in 100 consecutive runs on certification datasets.
* **RTO Limit:** Recovery time from checkpoints under **500ms**.
* **Zero Automatic Merges:** Enforced by supervisor validations (100% pass on block tests).
* **Sandbox Verification:** zero writes permitted outside approved sandbox paths.

---

## 2. Production Deployment Workflow Diagram

```mermaid
graph TD
    BuildPass([CI/CD Build Successful]) --> RunCert[1. Run E2E Certification Suite]
    RunCert --> VerifyCert{"2. All Domains PASS?"}
    VerifyCert -- No --> Abort[ABORT DEPLOYMENT]
    
    VerifyCert -- Yes --> FreezeRegistry[3. Freeze Registries startup]
    FreezeRegistry --> HealthCheck[4. Verify Startup Health status]
    
    HealthCheck --> HealthOK{"5. Health Status OK?"}
    HealthOK -- No --> Rollback[6. Trigger Rollback Deployment]
    
    HealthOK -- Yes --> Traffic[7. Route Production Traffic]
    Traffic --> Monitor[8. Observability Hook Telemetry Run]
    
    Monitor --> MonitorOK{"9. Anomalies Detected?"}
    MonitorOK -- Yes --> Rollback
    MonitorOK -- No --> Complete([DEPLOYMENT COMPLETE])
```

---

## 3. Deployment Checklist

### Pre-Deployment Tasks
* `[ ]` Execute E2E certification test suite locally and in staging environments.
* `[ ]` Verify that all reports (Phase 1 to Phase 9) are frozen.
* `[ ]` Verify directory sandbox parameters are set to read-only for system directories.
* `[ ]` Confirm that no LLM autonomous execution logic is present in active code modules.

### Deployment Tasks
* `[ ]` Deploy the modular package codes (`bbc_aos/core/`, `loops/`, `memory/`, `knowledge/`, `integration/`).
* `[ ]` Run startup sequencing tests, verifying registry freezes.
* `[ ]` Query subsystem health status endpoints (`HealthManager.check_subsystem_health()`).

### Post-Deployment Tasks
* `[ ]` Perform 5 test transactions with tracing UUIDs.
* `[ ]` Run ReplayEngine to verify that test transactions re-execute and match hashes.
* `[ ]` Verify that the append-only `IntegrationAuditLog` has compiled all step entries.
