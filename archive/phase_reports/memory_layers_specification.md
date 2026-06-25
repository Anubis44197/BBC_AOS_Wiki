# Memory Layers Specification - Phase 7E

This document specifies the data representations, attributes, and roles for each of the five memory layers in the `bbc_aos` framework.

---

## 1. Working Memory

Working Memory captures transient, highly dynamic data needed during active execution.

* **Contents:**
  * Active execution state variables.
  * Active Loop Engine states.
  * Iteration `LoopCheckpoint` files.
* **Storage Representation:** Local memory dictionaries backed by serialized temporary JSON files on disk.
* **Key Fields:**
  * `session_id` (UUIDv4)
  * `current_step_index` (int)
  * `active_checkpoints` (List[LoopCheckpoint])

---

## 2. Episodic Memory

Episodic Memory archives the chronological history of completed tasks, runs, and sessions.

* **Contents:**
  * Execution log histories.
  * Task decompositions and intermediate outputs.
  * Replay artifacts.
* **Storage Representation:** Append-only log files (`.bbc/logs/history.jsonl`).
* **Key Fields:**
  * `task_id` (UUIDv4)
  * `execution_steps` (List[Dict[str, Any]])
  * `replay_artifacts_paths` (List[str])

---

## 3. Semantic Memory

Semantic Memory holds structured, long-term project knowledge and recipes.

* **Contents:**
  * AST symbol dependency graphs (`symbol_graph.py` outputs).
  * Central project metadata and index indexes.
  * Verified BBC recipe templates.
* **Storage Representation:** Graph mappings, index tables, and recipe JSON files.
* **Key Fields:**
  * `symbol_id` (str)
  * `dependencies` (List[str])
  * `recipe_schema` (Dict[str, Any])

---

## 4. Human Knowledge Memory

Human Knowledge Memory stores documents and annotations authored directly by humans.

* **Contents:**
  * Obsidian markdown notes.
  * Human-curated instructions.
  * Project wiki pages.
* **Storage Representation:** Markdown files (`.obsidian/` or `wiki/` directories).
* **Key Fields:**
  * `document_id` (str)
  * `author` (str)
  * `content` (str)
* **Isolation Rule:** System components and agents cannot write to or modify this layer. Its contents are read-only and must pass through cross-layer promotion validation with human approval before they can influence Semantic Memory.

---

## 5. Experience Memory

Experience Memory stores generalized patterns, traces, and lessons from previous runs to speed up execution.

* **Contents:**
  * Traces of successful executions.
  * Reusable workflow plans.
  * Replay experience logs.
* **Storage Representation:** Trace profiles and workflow mappings (`experience/` directory).
* **Key Fields:**
  * `experience_id` (UUIDv4)
  * `success_metric` (float)
  * `workflow_blueprint` (Dict[str, Any])
* **Reference Constraints:** May only reference nodes in Semantic Memory. It is strictly forbidden from directly updating or adding nodes in Semantic Memory.
