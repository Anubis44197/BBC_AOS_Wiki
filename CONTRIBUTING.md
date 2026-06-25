# Contributing to BBC-AOS

Thank you for your interest in contributing to BBC-AOS! To maintain the strict determinism and safety guarantees of the system, please adhere to the following guidelines:

## Code Layout
The repository uses the standard `src/` layout:
* `src/bbc_aos/`: Core library package.
* `tests/`: Automated unit, integration, and E2E regression test suites.
* `docs/`: User guides, architecture documents, and API references.
* `examples/`: Developer recipes.
* `tools/`: Helper utilities.

## Testing Guidelines
* All modifications must be fully covered by automated test cases under `tests/`.
* Run pytest to verify all tests pass:
  ```bash
  pytest tests/
  ```
* Running final certification checks is mandatory:
  ```bash
  python tools/run_final_certification.py
  ```
* All changes must maintain **100% E2E determinism** and zero-drift metrics.
