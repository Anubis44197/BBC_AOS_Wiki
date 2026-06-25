# AgentOrchestrator Flow API Contract Report - Phase 11F

This report specifies the API contracts, inputs, outputs, and JSON schemas for the `AgentOrchestrator` methods.

---

## 1. API Endpoints and Signatures

The `AgentOrchestrator` class exposes the following public Python API:

### `execute_goal`
Starts a sequential E2E execution from scratch.
* **Signature:**
  ```python
  def execute_goal(
      self,
      goal_id: str,
      goal_description: str,
      trace_id: str,
      replay_id: str,
      context_data: Optional[Dict[str, Any]] = None,
  ) -> Dict[str, Any]
  ```
* **Returns:** Summary status dictionary.

### `resume_execution`
Resumes an execution from the next uncompleted stage.
* **Signature:**
  ```python
  def resume_execution(self, trace_id: str, replay_id: str) -> Dict[str, Any]
  ```
* **Returns:** Summary status dictionary.

### `rollback_execution`
Rolls back to a checkpoint stage and immediately resumes execution.
* **Signature:**
  ```python
  def rollback_execution(self, trace_id: str, replay_id: str, target_stage: str) -> Dict[str, Any]
  ```
* **Returns:** Summary status dictionary.

### `get_execution_status`
Retrieves the status summary of a goal execution.
* **Signature:**
  ```python
  def get_execution_status(self, trace_id: str, replay_id: str) -> Dict[str, Any]
  ```
* **Returns:** Summary status dictionary.

### `resume_from_checkpoint`
Registers state from a serialized checkpoint and resumes execution.
* **Signature:**
  ```python
  def resume_from_checkpoint(self, checkpoint: Dict[str, Any]) -> Dict[str, Any]
  ```
* **Returns:** Summary status dictionary.

### `rollback_to_checkpoint`
Resets the execution state to a target stage checkpoint without resuming.
* **Signature:**
  ```python
  def rollback_to_checkpoint(self, trace_id: str, replay_id: str, target_stage: str) -> Dict[str, Any]
  ```
* **Returns:** Summary status dictionary of the rolled-back state.

---

## 2. JSON Schema Contracts

### Summary Status Dictionary
Every public method returning a status summary complies with the following structure:

```json
{
  "goal_id": "goal_id_string",
  "goal_description": "description_string",
  "trace_id": "trace_id_string",
  "replay_id": "replay_id_string",
  "current_stage": "planner|context|coder|tester|verify",
  "status": "IN_PROGRESS|COMPLETED|FAILED|REJECTED",
  "checkpoints": ["planner", "context", "coder", "tester", "verify"],
  "outputs": {
    "planner_result": {},
    "context_result": {},
    "coder_result": {},
    "tester_result": {},
    "verify_result": {}
  }
}
```
