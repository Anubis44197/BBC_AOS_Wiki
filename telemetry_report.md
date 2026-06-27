# Telemetry Report

Phase: C13 Real User Pilot Hardening
Date: 2026-06-27
Mode: No commits, no pushes

## Fix

`bbc ask --shadow` now exposes per-run metrics:

- `tokens_before`
- `tokens_after`
- `compression_ratio`
- `artifacts_generated`
- `wiki_notes_created`
- `execution_latency`

Metrics are displayed in CLI output, persisted in execution notes, and written to `.bbc/logs/integration_audit.jsonl` as `execution_telemetry`.

## Smoke Output

```text
[ASK] Telemetry:
[ASK]   tokens_before: 435
[ASK]   tokens_after: 333
[ASK]   compression_ratio: 1.31
[ASK]   artifacts_generated: 5
[ASK]   wiki_notes_created: 5
[ASK]   execution_latency: 34
```

## Persistence

Execution note telemetry: PASS.

Audit log telemetry: PASS.

Audit event type:

```text
execution_telemetry
```

## Notes

Token counts are deterministic estimates from workspace text content. The packed token value uses the existing BBC-AOS benchmark ratio.

Verdict: PASS.
