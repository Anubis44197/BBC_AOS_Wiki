# Shadow Mode Report

Implemented `bbc ask --shadow "<goal>"`.

Behavior:
- Runs Planner, Context, Coder, Tester, and Verification.
- Skips approval request.
- Skips commit.
- Performs no file changes.
- Prints files that would change and estimated risk.

Constraint:
- Human approval remains mandatory for non-shadow commits.
