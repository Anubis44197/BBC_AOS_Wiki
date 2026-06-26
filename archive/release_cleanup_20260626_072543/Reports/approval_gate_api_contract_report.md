# Human Approval Gates API Contract Report - Phase 11H

This report specifies the API contracts, method signatures, parameter definitions, and return formats for the `ApprovalManager`.

---

## 1. API Method Specifications

The `ApprovalManager` class exposes the following public API:

### `request_approval`
Creates a request and routes it based on risk.
* **Signature:**
  ```python
  def request_approval(
      self,
      trace_id: str,
      replay_id: str,
      risk_level: str,
      commit_payload: Dict[str, Any],
  ) -> Dict[str, Any]
  ```
* **Returns:** Serialized `ApprovalResult` dictionary.

### `approve`
Approves a pending or escalated request.
* **Signature:**
  ```python
  def approve(self, approval_id: str) -> Dict[str, Any]
  ```
* **Returns:** Serialized `ApprovalResult` dictionary with status `"APPROVED"`.

### `reject`
Rejects a pending or escalated request.
* **Signature:**
  ```python
  def reject(self, approval_id: str) -> Dict[str, Any]
  ```
* **Returns:** Serialized `ApprovalResult` dictionary with status `"REJECTED"`.

### `timeout`
Expires a pending request.
* **Signature:**
  ```python
  def timeout(self, approval_id: str) -> Dict[str, Any]
  ```
* **Returns:** Serialized `ApprovalResult` dictionary with status `"EXPIRED"`.

### `escalate`
Escalates a pending request.
* **Signature:**
  ```python
  def escalate(self, approval_id: str) -> Dict[str, Any]
  ```
* **Returns:** Serialized `ApprovalResult` dictionary with status `"ESCALATED"`.

### `rollback_request`
Rolls back requests mappings to the latest checkpoint.
* **Signature:**
  ```python
  def rollback_request(self, approval_id: str) -> Dict[str, Any]
  ```
* **Returns:** Rollback summary dictionary.

### `get_status`
Queries approval status details from memory or the audit log file.
* **Signature:**
  ```python
  def get_status(self, approval_id: str) -> Dict[str, Any]
  ```
* **Returns:** Status details dictionary.

---

## 2. Payload Schemas

### `ApprovalResult` Serialization Format
```json
{
  "approval_id": "approval_id_string",
  "approval_hash": "sha256_hash_string",
  "status": "APPROVED|REJECTED|PENDING|ESCALATED|EXPIRED",
  "timestamp": "iso8601_timestamp_string"
}
```

### `ApprovalAuditLog` Format (`approval_audit.jsonl`)
```json
{
  "trace_id": "tr_1",
  "replay_id": "rp_1",
  "approval_id": "app_xxx",
  "approval_hash": "approval_hash_sha256",
  "status": "PENDING|APPROVED|REJECTED|EXPIRED|ESCALATED|ROLLED_BACK",
  "timestamp": "2026-06-24T20:00:00Z",
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"
}
```
