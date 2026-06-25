# Implementation Plan - Production CI/CD & Click CLI Integration

This plan outlines the final productization steps for BBC-AOS:
1. Configuring the final packaging definitions in `pyproject.toml` (Setuptools, Ruff, MyPy, PyTest).
2. Implementing the robust Click CLI under `src/bbc_aos/main.py`.
3. Creating the GitHub Actions CI/CD workflows (`ci.yml` and `certification.yml`).
4. Running E2E packaging validation, including pip installs, wheel builds, and running commands in a simulated clean environment.

## User Review Required

> [!IMPORTANT]
> * **CLI Implementation**: We will implement Click commands (`init`, `index`, `ask`, `doctor`, `replay`, `benchmark`, `obsidian connect`) in `src/bbc_aos/main.py` referencing standard subsystems.
> * **Build System**: We will switch `pyproject.toml` build system to Setuptools to align with `[tool.setuptools.packages.find]` as recommended.
> * **GitHub Workflows**: We will add `.github/workflows/ci.yml` and `.github/workflows/certification.yml` to trigger automatically.

## Open Questions

None. The requirements are fully detailed and specified.

## Proposed Changes

### 1. Build System & Packaging Configuration

#### [MODIFY] [pyproject.toml](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/pyproject.toml)
* Update build-system to use `setuptools>=61.0.0` and `wheel`.
* Define `[tool.setuptools.packages.find]` with `where = ["src"]`.
* Update `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `addopts = ["--import-mode=importlib"]`.
* Add `[tool.ruff]` with `line-length = 100`.
* Add `[tool.mypy]` with `strict = true`.

---

### 2. User CLI Surface

#### [MODIFY] [main.py](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/src/bbc_aos/main.py)
* Replace stub file with a fully functional Click CLI interface.
* Expose:
  * `bbc init`: Sets up the `.bbc/` runtime folders and configuration templates.
  * `bbc index [path]`: Scans code files, extracts symbols via `SymbolExtractor`, and registers the symbol graph to memory.
  * `bbc ask "[query]"`: Spawns the sequential `AgentOrchestrator` E2E execution pipeline, processes stages, runs validation, requests human approval, and invokes `CommitManager` upon approval.
  * `bbc doctor`: Executes health sweeps via `SubsystemRegistry` and `IntegrationOrchestrator` and checks registry lock states.
  * `bbc replay <trace_id>`: Reconstructs agent execution sequences from the audit log using `ReplayEngine`.
  * `bbc benchmark`: Runs performance, hallucination, and token compression metrics.
  * `bbc obsidian connect [vault_path]`: Registers and indexes an Obsidian knowledge vault path.

---

### 3. CI/CD Pipeline

#### [NEW] [ci.yml](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/.github/workflows/ci.yml)
* Runs on push/pull request to main.
* Stages:
  1. Checkout code.
  2. Setup Python.
  3. Install dependencies (`pip install -e .[dev]`).
  4. Run Ruff linting.
  5. Run PyTest test suite.
  6. Build wheel (`python -m build`).
  7. Build docker image (`docker build -t bbc-aos:latest .`).

#### [NEW] [certification.yml](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/.github/workflows/certification.yml)
* Runs certification.
* Stages:
  1. Checkout code.
  2. Setup Python.
  3. Run `python tools/run_final_certification.py`.

---

### 4. Manifest Configuration

#### [MODIFY] [MANIFEST.in](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/MANIFEST.in)
* Verify files included in build: source code, readme, license, pyproject.toml, etc.

## Verification Plan

### Automated Tests
* Run `pytest` to ensure all 59+ tests pass successfully.
* Run `tools/run_final_certification.py` locally.

### Manual Packaging Verification
1. Run `pip install -e .`
2. Build wheel package: `python -m build`
3. Install package: `pip install dist/*.whl`
4. Execute `bbc --help` to confirm CLI surface is active and fully functional.
