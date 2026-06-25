# Commit Subsystem Pipeline API Contract Report - Phase 11G

This report specifies the API contracts, method signatures, parameter specifications, and return types for the `CommitManager` class.

---

## 1. API Method Specifications

The `CommitManager` class exposes the following public API:

### `execute_commit`
Validates, snapshots, and applies code changes to files.
* **Signature:**
  ```python
  def execute_commit(
      self,
      verdict_data: Dict[str, Any],
      code_diff: Dict[str, Any],
      workspace_root: str,
  ) -> Dict[str, Any]
  ```
* **Returns:** Serialized `CommitResult` dictionary with status `"SUCCESS"`.

### `dry_run_commit`
Validates policies, limits, and sandboxes without writing to the disk.
* **Signature:**
  ```python
  def dry_run_commit(
      self,
      verdict_data: Dict[str, Any],
      code_diff: Dict[str, Any],
      workspace_root: str,
  ) -> Dict[str, Any]
  ```
* **Returns:** Serialized `CommitResult` dictionary with status `"DRY_RUN"`.

### `rollback_commit`
Rolls back the latest commit transaction in the stack.
* **Signature:**
  ```python
  def rollback_commit(
      self,
      trace_id: str,
      replay_id: str,
      workspace_root: str,
  ) -> Dict[str, Any]
  ```
* **Returns:** Status dictionary showing `"ROLLED_BACK"`.

### `get_commit_status`
Queries commit metadata from memory or the audit log file.
* **Signature:**
  ```python
  def get_commit_status(self, commit_hash: str) -> Dict[str, Any]
  ```
* **Returns:** Status details dictionary.

---

## 2. Payload Schemas

### `CommitResult` Serialization Format
```json
{
  "commit_hash": "sha256_hash_string",
  "trace_id": "trace_id_string",
  "replay_id": "replay_id_string",
  "timestamp": "iso8601_timestamp_string",
  "status": "SUCCESS|DRY_RUN",
  "affected_files": ["file1.py", "file2.py"]
}
```

### `CommitAuditLog` Format (`commit_audit.jsonl`)
Each line contains a JSON object:
```json
{
  "trace_id": "tr_1",
  "replay_id": "rp_1",
  "deterministic_hash": "verdict_det_hash",
  "commit_hash": "commit_hash_sha256",
  "timestamp": "2026-06-24T20:00:00Z",
  "affected_files": ["module_1.py"]
}
```
