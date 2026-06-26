# Final Benchmark Report

Result: LIMITED

Benchmark harness:
- `tools/benchmark_real_repositories.py`

Repositories listed:
- Django
- FastAPI
- Flask
- Requests
- React

Metrics tracked:
- token reduction
- hallucinated files
- wrong edits
- rollback rate
- human rejection rate
- latency
- replay fidelity

Execution result:
- Harness executed successfully.
- Current harness records deterministic placeholder metrics.
- Real clone/run comparison against external repositories was not executed in this release pass.

Blocking issue:
- Public claim-ready benchmark metrics require a network-enabled benchmark runner and real repository execution.
