# Risk Report - Legacy BBC Migration

This report highlights the operational, security, and performance risks identified in the legacy BBC repository and provides mitigation strategies for the BBC-AOS implementation.

---

## 1. Security Risks

### A. Arbitrary Shell Command Execution
* **Risk:** High
* **Details:** `bbc_core/native_adapter.py` directly builds shell commands and runs them via `subprocess.Popen` or `subprocess.run` to interact with Git or run scripts. If an agent compromises the repository context, it could inject malicious commands into the system.
* **Mitigation:**
  * Avoid raw subshell spawning. Use native Python libraries (such as GitPython for git commands, or standard library filesystem functions).
  * Introduce an execution sandbox or containerized environment for any external scripts.

### B. Spoofing of "Math" Origins
* **Risk:** Medium
* **Details:** `bbc_scalar.py` uses metadata serialization (`origin: "math"` vs. `"semantic"`). In `from_dict()`, it forces deserialized inputs to `"semantic"` to prevent origin spoofing. However, internal state merges still present minor boundary check vulnerabilities.
* **Mitigation:**
  * Enforce strict, cryptographically verified boundaries for math-origin variables.
  * Encapsulate mathematical calculations in a separate, compiled library or isolate them in memory.

---

## 2. Performance & Resource Risks

### A. Synchronous CPU-Bound Math (Blocking IO)
* **Risk:** Medium
* **Details:** Singular matrix condition checks, pseudo-inverses, and Sinkhorn iterations are computed synchronously. When `http_server.py` processes multiple concurrent JSON-RPC requests, CPU blocking will occur, degrading the latency of client agents.
* **Mitigation:**
  * Delegate matrix operations to a thread pool or an asynchronous execution worker.
  * Optimize matrix operations using vectorized NumPy operations.

### B. High File System I/O Overheads
* **Risk:** Medium
* **Details:** `telemetry.py` writes event entries to `.bbc/logs/telemetry.jsonl` on every single event, opening and closing the file for each log. Under heavy loads, this disk writing will bottleneck performance.
* **Mitigation:**
  * Implement an asynchronous memory buffer for telemetry logs.
  * Flush telemetry events to disk in batches or write to a high-speed SQLite database.

---

## 3. Integration & Operational Risks

### A. High Dependency on Local Paths
* **Risk:** Medium
* **Details:** Many legacy scripts use relative directory lookups (e.g., `os.path.dirname(os.path.dirname(__file__))`) to locate `.bbc` folders. This fails if the CLI is executed from outside the workspace root.
* **Mitigation:**
  * Enforce a strict Workspace Root environment variable configuration.
  * Reject execution if the Workspace Root is invalid or missing.

### B. Fragile Scraping Targets
* **Risk:** High
* **Details:** The scrapers (Mynet, Yahoo) described in the specs are extremely fragile. A single change in the provider's layout or rate-limit policy can break the data acquisition layer.
* **Mitigation:**
  * Implement clean error boundaries and fallback pipelines (e.g., Yahoo -> local cache -> İş Yatırım).
  * Rotate User-Agents and randomize request intervals.
