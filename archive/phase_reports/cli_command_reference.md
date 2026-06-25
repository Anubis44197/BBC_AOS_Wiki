# Phase 13A - CLI Command Reference

This document provides a detailed command syntax reference for the `bbc` CLI tool.

---

## 1. Commands Specification

### `bbc init`
* **Syntax**: `bbc init [--force]`
* **Arguments**:
  * `--force`: Forcefully overwrites any existing `.bbc/` folder.
* **Expected Output**:
  ```
  [INFO] Initializing bbc workspace...
  [INFO] Created .bbc/ folder structure.
  [INFO] Initialized local sqlite metadata database.
  [SUCCESS] Workspace initialized. Run 'bbc index .' to build codebase graphs.
  ```

### `bbc index`
* **Syntax**: `bbc index [target_path] [--exclude pattern]`
* **Arguments**:
  * `target_path`: The directory containing codebase files (defaults to `.`).
  * `--exclude`: Glob pattern of files or directories to ignore (e.g. `tests/*`).
* **Expected Output**:
  ```
  [INFO] Scanning codebase for python symbols...
  [INFO] Processed 45 files, extracted 124 classes and 312 functions.
  [INFO] Compiled Call Graph. SimHash indexes registered.
  [SUCCESS] Codebase successfully indexed in memory.
  ```

### `bbc start`
* **Syntax**: `bbc start [--daemon] [--config path]`
* **Expected Output**:
  ```
  [INFO] Starting BBC-AOS Sidecar Service...
  [INFO] Loading local state memory...
  [SUCCESS] Sidecar active. Daemon PID: 12453
  ```

### `bbc serve`
* **Syntax**: `bbc serve [--port port] [--host address]`
* **Arguments**:
  * `--port`: Target TCP port (default: `8080`).
  * `--host`: Interface bind address (default: `127.0.0.1`).
* **Expected Output**:
  ```
  [INFO] Launching JSON-RPC Sidecar API Server...
  [INFO] Binding to 127.0.0.1:8080
  [SUCCESS] Server active. Listening for IDE extension RPC requests.
  ```

### `bbc ask`
* **Syntax**: `bbc ask "prompt" [--sandbox-only] [--no-approval]`
* **Arguments**:
  * `prompt`: The natural language request.
  * `--sandbox-only`: Run only in transient copy mode.
  * `--no-approval`: Disables automated LOW approvals (forces approval wait).

### `bbc doctor`
* **Syntax**: `bbc doctor`
* **Expected Output**:
  ```
  [DOCTOR] Running platform diagnostics...
  - Subsystem Core: OK
  - Subsystem Memory: OK
  - Subsystem Knowledge: OK
  - Registry Freeze Protection: ACTIVE
  - Health sweeps: ACTIVE (Graceful degradation hooks registered)
  [SUCCESS] All checks passed. Platform is stable.
  ```
