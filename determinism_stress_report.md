# Determinism Stress Report

Result: PASS WITH SCOPE LIMITATION

Executed:
- 1,000 iterations per scenario
- scenarios: bugfix, feature, refactor, review, test

Observed:
- unique hashes: 1 per scenario
- unique outputs: 1 per scenario
- unique replay ids: 1 per scenario
- zero variance: true

Scope limitation:
- documentation generation was requested in the validation brief but is not covered by the existing deterministic stress script.
