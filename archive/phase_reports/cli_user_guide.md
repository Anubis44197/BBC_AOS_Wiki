# Phase 13A - CLI User Guide

This guide describes the developer command-line experience for the `bbc` tool.

---

## 1. Overview

The `bbc` Command-Line Interface (CLI) is the primary developer interface for initializing workspaces, building indexes, starting the sidecar engine, launching agent pipelines, and replaying historic transactions.

---

## 2. Command Catalog

| Command | Usage | Description |
| :--- | :--- | :--- |
| **`bbc init`** | `bbc init [--force]` | Initializes the `.bbc/` configuration folder in the current directory. |
| **`bbc index`** | `bbc index [path]` | Scans target codebase paths, extracts symbol graphs, and builds SimHash indices. |
| **`bbc start`** | `bbc start [--daemon]` | Launches the local sidecar orchestrator and memory layer. |
| **`bbc serve`** | `bbc serve [--port 8080]` | Exposes the JSON-RPC API endpoint for IDE (Gemini IDE / VS Code) integrations. |
| **`bbc ask`** | `bbc ask "goal description"` | Dispatches a developer request directly to the `AgentOrchestrator` chain. |
| **`bbc replay`** | `bbc replay <replay_id>` | Re-runs a historic transaction using recorded audit log events. |
| **`bbc benchmark`** | `bbc benchmark [dataset]` | Runs the hallucination and token reduction benchmark suites. |
| **`bbc sync-obsidian`** | `bbc sync-obsidian` | Syncs Obsidian vault markdown notes and promotes designs. |
| **`bbc status`** | `bbc status` | Queries active execution statuses, checkpoints, and pending approvals. |
| **`bbc doctor`** | `bbc doctor` | Verifies subsystem health status and checks registry freeze states. |

---

## 3. Standard Developer Workflows

### Setup and Indexing
1. Initialize the workspace:
   ```bash
   bbc init
   ```
2. Build code indexes:
   ```bash
   bbc index .
   ```

### Launching Agent Code Modifications
1. Query a task:
   ```bash
   bbc ask "Fix bug in scalar matrix calculations"
   ```
2. Check pending approvals:
   ```bash
   bbc status
   ```
3. Approve a request:
   ```bash
   bbc approve <approval_id>
   ```
