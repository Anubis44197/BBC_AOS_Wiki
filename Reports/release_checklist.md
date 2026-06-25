# Phase 13A - Release Checklist

This document serves as the operational release checklist before promoting BBC-AOS to v1.0.0.

---

## Pre-Release Checklist

* **`[ ]` Code Integrity Checks**
  * `[ ]` Run PEP 8 syntax checks (Flake8 / Black formatter).
  * `[ ]` Verify type-hint coverage (MyPy verification passes).
  * `[ ]` Confirm all tests under `/tests` pass (100% test success rate).

* **`[ ]` Build & Package Checks**
  * `[ ]` Build source and binary wheel package distributions.
  * `[ ]` Install the built package locally via `pip install dist/*.whl`.
  * `[ ]` Confirm `bbc --help` executes and returns correct command usage lists.

* **`[ ]` Operational Verification**
  * `[ ]` Run `bbc doctor` and verify all subsystems report health status `OK`.
  * `[ ]` Test `bbc init` in a fresh directory and check that `.bbc/` is created.
  * `[ ]` Verify call graph construction by indexing the examples.

* **`[ ]` Documentation Sync**
  * `[ ]` Check that `README.md` is updated and contains the JWT authentication usage scenario.
  * `[ ]` Confirm all phase documentation reports are synchronized to the `/Reports` directory.
