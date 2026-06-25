# Phase 13A - Packaging Strategy

This document details the standard Python packaging configuration and the cross-platform support matrix for releasing the `bbc-aos` tool.

---

## 1. CLI Commands Packaging Goals

The packaged distribution must support standard pip installations and native command initializations:

* **Installation**:
  ```bash
  pip install bbc-aos
  ```
* **Initialization**:
  ```bash
  bbc init
  ```
* **Codebase Indexing**:
  ```bash
  bbc index .
  ```
* **Orchestrator Boot**:
  ```bash
  bbc start
  ```

---

## 2. Python Package Configuration (`pyproject.toml`)

Below is the standard configuration layout using `hatchling` as the build backend:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "bbc-aos"
version = "1.0.0"
description = "Best-practice Blast-radius Codebase Agentic Orchestration System"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "click>=8.1.0",
    "pydantic>=2.0.0",
    "psutil>=5.9.0",
    "watchdog>=3.0.0"
]

[project.scripts]
bbc = "bbc_aos.main:cli"
```

---

## 3. Platform Support Matrix

The platform is officially certified across the following environments:

| Platform | Support Status | Native Integration | File System Locking |
| :--- | :--- | :--- | :--- |
| **Docker** | **Certified** | Exposes JSON-RPC sidecar API | Native Unix file locks |
| **Windows 11 / 10** | **Certified** | PowerShell cli wrappers | Win32 API slot handling |
| **Linux (Ubuntu/RHEL)**| **Certified** | Shell cli wrappers | POSIX file locking |
| **MacOS (macOS 12+)** | **Certified** | Zsh cli wrappers | BSD file locking |

---

## 4. Release Build Instructions

1. Install build dependencies:
   ```bash
   pip install --upgrade build twine
   ```
2. Build binary wheel and source distributions:
   ```bash
   python -m build
   ```
3. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```
