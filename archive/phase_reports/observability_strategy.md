# Observability Strategy - Phase 10A

This document details the logging, monitoring, and tracing hooks required to ensure full observability across BBC-AOS.

## 1. Unified Telemetry Logging Schema

All subsystems write audit-related entries to a unified telemetry stream (`telemetry.jsonl`) following JSON-RPC 2.0 extension standards.

```json
{
  "timestamp": "2026-06-24T18:55:00.123Z",
  "trace_id": "tr_902a7b8e-c901-4b72-b88a-3c1c98114fcf",
  "replay_id": "rp_4d5b2c7e-8f90-4e12-ac8b-11bc90a09cef",
  "deterministic_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "subsystem": "loop | memory | knowledge | core | agent",
  "level": "INFO | WARN | ERROR | FATAL",
  "event_type": "subsystem_dispatch | checkpoint_created | sync_commit | aura_calibrated",
  "message": "Step executed successfully",
  "payload": {}
}
```

---

## 2. Observability Hook Registrations

Observability is maintained through hooks exposed at managers and engine supervisors:

* **`before_read()` / `after_read()`**: Logs vault index sweeps and scans.
* **`before_propose()` / `after_propose()`**: Traces sync proposal generation and metrics.
* **`before_sync()` / `after_sync()`**: Records committed sync iterations.
* **`on_approval_required()`**: Dispatched when manual human authorization is blocked waiting for user action.
* **`on_replay()`**: Fired during replay rehydration.
* **`before_iteration()` / `after_iteration()`**: Traces loop engine iteration counts and resource budgets.
* **`on_failure()` / `on_timeout()`**: Intercepted by supervisors during crashes or budget depletion.

---

## 3. Diagnostic Playbacks

* **Correlation Auditing:** The `ReplayEngine` matches all events in the telemetry stream by `trace_id` or `replay_id`.
* **Zero-Variance Testing:** In production, playbacks must reconstruct identical state hashes to verify system-wide stability.
