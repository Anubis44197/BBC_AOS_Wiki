# Hallucination Validation Report

Result: BLOCKED

Executed:
- 200 synthetic hallucination tasks

Inputs referenced:
- nonexistent files
- nonexistent classes
- nonexistent functions
- invalid imports
- missing symbols

Observed:
- blocked: 160/200
- allowed: 40/200
- hallucinated write allowance rate: 20%

Blocking issue:
- Lowercase nonexistent function references such as `missing_function_123()` are not detected as invalid symbols by the current hallucination detector.
