# Shadow Mode Integrity Report

Result: BLOCKED

Executed:
- 20 real `bbc ask --shadow "fix login bug"` runs after init and index
- all 20 runs exited successfully

Observed:
- source file `app.py` remained unchanged
- full workspace checksum changed

Changed files:
- `.bbc/logs/telemetry.jsonl`
- `.bbc/state/*_state.json`
- `.bbc/reflections/*.json`

Conclusion:
- Shadow mode satisfies no source-code write behavior in this sample.
- Shadow mode does not satisfy the stricter requirement of no file modifications at all.
