# Phase C8: Real Repository Benchmark Suite

Goal: compare BBC OFF vs BBC ON on real repositories.

Target repositories:
- Django
- FastAPI
- Requests
- Flask
- React

Metrics:
- Hallucinated files
- Wrong edits
- Token usage
- Rollback rate
- Human rejection rate
- Latency

Protocol:
1. Clone each repository into an isolated benchmark workspace.
2. Run the same task set with BBC controls disabled.
3. Run the same task set with BBC controls enabled.
4. Record patch scope, verification outcome, rollback events, and user approval state.
5. Publish aggregate results in `Reports/real_repository_benchmark_report.md`.

BBC-AOS must not push benchmark changes to upstream repositories.
