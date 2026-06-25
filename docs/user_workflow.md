# BBC-AOS User Workflow Guide

This guide describes the complete onboarding and development workflow for developers using BBC-AOS.

## 1. Installation

Install the package globally or in your virtual environment:
```bash
pip install bbc-aos
```

---

## 2. Workspace Initialization

Run the initialization command at the root of your project directory:
```bash
cd my_project
bbc init
bbc wiki init
```
This sets up:
* `.bbc/`: The silent background database and state tracker folders.
* `BBC_Wiki/`: The local, human-readable markdown project documentation structure.

---

## 3. Codebase Indexing

Compile your codebase's initial symbol graph and register it to semantic memory:
```bash
bbc index .
```
This indexes your classes, functions, and imports, constructing the dependency mapping that prevents hallucinated file edits.

---

## 4. Obsidian Vault Integration (Optional)

If you use Obsidian, connect your vault to let BBC-AOS populate proposal notes automatically:
```bash
bbc obsidian connect "/path/to/your/obsidian/vault"
```
Once connected, you can open your Obsidian vault and review note proposals directly inside the UI.

---

## 5. Daily Task Execution Flow

### Step A: Ask a Task
Request code changes or analysis:
```bash
bbc ask "add JWT authentication to authentication controller"
```

### Step B: Background Execution
The system silently executes the task pipeline:
1. **Decomposes Goal**: Spawns plans deteministically.
2. **Filters Context**: Gathers minimal relevant symbols.
3. **Drafts Code changes**: Generates code patch in a safe workspace sandbox.
4. **Validates & Verifies**: Executes unit/integration test sweeps and runs safety check checks.

### Step C: On-Screen Reporting & Manual Approval
The CLI outputs:
* Task status details.
* Safety verification verdict.
* **Approval Request** (If the task risk level is MEDIUM or higher, the CLI prompts for confirmation: `Do you authorize this transaction commit? [y/N]`).

### Step D: Git Commit & Wiki Note Proposal
Upon verification and approval:
* The changes are committed to the local git branch.
* A markdown note proposal is created under `BBC_Wiki/Approvals/prop_<replay_id>.md` (and inside the Obsidian vault if connected).

---

## 6. Reviewing and Promoting Wiki Notes

Review the note proposal under `BBC_Wiki/Approvals/`:
* To accept and promote:
  ```bash
  bbc wiki approve prop_<replay_id>.md
  ```
  This moves the note to `Executions/` and registers it to semantic memory.
* To reject:
  ```bash
  bbc wiki reject prop_<replay_id>.md
  ```
  This moves the note to `Approvals/rejected/`.
