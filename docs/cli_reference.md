# CLI Command Reference

Detailed usage parameters and options for the `bbc` CLI tool.

## `bbc init`
Initializes a new local workspace directory.
* **Usage**: `bbc init [options]`
* **Options**:
  * `--force`: Force recreation of local `.bbc/` folder if it already exists.

## `bbc index`
Indexes codebase symbols, docstrings, classes, and methods.
* **Usage**: `bbc index [path] [options]`
* **Options**:
  * `--exclude`: Glob pattern to ignore during indexing (e.g. `--exclude "**/tests/**"`).
  * `--simhash-threshold`: Distance boundary to identify similar documents (default: 3).

## `bbc start`
Starts the JSON-RPC interface sidecar server.
* **Usage**: `bbc start [options]`
* **Options**:
  * `--port`: Port to listen on (default: 8080).
  * `--host`: Interface host binding (default: 127.0.0.1).

## `bbc doctor`
Diagnoses the health of all registered agent registries, memory lock files, and database connections.
* **Usage**: `bbc doctor`
