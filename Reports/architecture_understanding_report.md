# Architecture Understanding Report - BBC-AOS

This report details the system architecture, implementation order, major components, risks, and open questions identified in the BBC Agent Operating System (BBC-AOS) specifications.

---

## 1. System Architecture

The BBC-AOS architecture is structured as a **hybrid decision and regulation system**, consisting of a deterministic mathematical guardrail (HMPU) and a data pipeline (TDFD + Stealth Scrapers) governed by a reinforcement learning brain (RLM).

```
 ┌────────────────────────────────────────────────────────┐
 │                      USER / AGENT                      │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Submits Action / Query)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │          HMPU CORE (Deterministic Guardrail)           │
 │  - OP-01: dC/dt (Entropy Noise Filter)                 │
 │  - OP-02: grad A (Dynamic Eşikleri Kalibrasyonu)       │
 │  - OP-03: P_t+1 (Nabız/Pertürbasyon Kararlılığı)       │
 │  - OP-04: F_perp (Orthogonal Context Projection)       │
 └──────────────────────────┬─────────────────────────────┘
                            │ (If perturbation < 0.50)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │                     RLM BRAIN                          │
 │  - BitNet CPU (Probabilistic Low-bit Decision)         │
 │  - Memory Buffer (Trap States & Historic Successes)    │
 └──────────────────────────┬─────────────────────────────┘
                            │ (Refines Request Strategy)
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │               TDFD ENGINE & SCRAPERS                   │
 │  - TDFD (T12 Phase Resonance Engine)                   │
 │  - Hayalet Mod (User-Agent Rotator, Jitter Delay)      │
 │  - Global Shadow Proxy Chain (ADR / Currency Fallback) │
 └────────────────────────────────────────────────────────┘
```

---

## 2. Major Components

### A. HMPU Core (Deterministic Layer)
* **Function:** Acts as a gatekeeper. It treats all streaming input/actions as points on a Riemann Manifold.
* **Key Mechanisms:**
  * **dC/dt (OP-01):** Analyzes Shannon Entropy. If a chunk consists mostly of high-entropy noise, it is ignored/filtered.
  * **grad A (OP-02):** Aura styling. Adjusts acceptability bounds depending on user interaction history.
  * **P_t+1 (OP-03):** Simulates the next state's eigenvalue stability. If perturbation exceeds 0.50, the action is blocked.
  * **F_perp (OP-04):** Context projection. Drops tools or information contextually unrelated to the target task.

### B. TDFD Engine & Data Acquisition Layer (Hybrid Layer)
* **Function:** Fetches BIST stock data and detects cyclical resonance patterns.
* **Key Mechanisms:**
  * **Resonance Detector:** Looks for periodic cycles (e.g., T12 cycle) instead of moving averages.
  * **Hayalet Mod:** Rotates headers and introduces 2-4 second random delays to scrape Yahoo/Mynet safely.
  * **Global Proxy:** Maps domestic stock symbols to US ADRs (`TKHVY` for `THYAO`) and converts them using real-time USD/TL rates.

### C. RLM Brain & BitNet CPU (Probabilistic/AI Layer)
* **Function:** Feeds historical results back into the system to guide future choices and prevent repetitive failure states (traps).
* **Key Mechanisms:**
  * **RLM Brain:** Reinforcement learning layer that runs "Rüya Modu" (Dream Mode) during idle periods to digest old buffer logs.
  * **BitNet Decision Engine:** Replaces complex nested conditional code (`if-else` blocks) with low-bit probabilistic weights.

---

## 3. Recommended Implementation Order (Roadmap)

To successfully transition from legacy code to the spec-compliant BBC-AOS, implementation must follow a bottom-up, test-driven path:

1. **Phase 1: Basic Infrastructure & Fallbacks**
   * Setup standard project config, DNA verification hash, and static fallbacks (e.g., USD/TL static rate configuration).
   * Implement **Hayalet Mod (Stealth Scraper)** with randomized timing and user-agent rotations.
2. **Phase 2: Mathematical Foundations (Deterministic HMPU)**
   * Implement Shannon Entropy algorithms for **OP-01 (dC/dt)**.
   * Write **OP-03 (P_t+1)** eigenvalue stability checks and state simulators.
   * Add **OP-04 (F_perp)** orthogonal projection.
3. **Phase 3: Financial Cycles & Proxies (TDFD)**
   * Move BIST data parsing logic into a structured pipeline.
   * Build the **TDFD Engine** for phase resonance calculations.
   * Build the **Global Proxy Chain** with ADR multipliers.
4. **Phase 4: Cognitive Feedback (RLM & BitNet)**
   * Build the RLM memory buffer and reward scoring structure.
   * Build the BitNet CPU probabilistic classifier to replace manual rule-based decision code.
   * Introduce "Rüya Modu" idle-state processing.

---

## 4. Key Architectural Risks

1. **Scraping Blockage (High Risk):** Despite Stealth Mode (Hayalet Mod), financial providers like Yahoo and Mynet frequently change anti-bot policies, which can break the data acquisition layer.
2. **Mathematical Complexity (Medium Risk):** Real-time eigenvalue calculation and manifold projection inside **HMPU** must be written in high-performance Python (using NumPy/SciPy) to stay within the **20 MB RAM** constraint under heavy loads.
3. **AI Non-Determinism (Medium Risk):** The RLM Brain must not interfere with the HMPU's deterministic guardrails; HMPU must remain the final arbiter of system safety.

---

## 5. Open Questions

1. **HMPU Target Inputs:** Is HMPU meant to inspect agent code execution changes, user inputs, or raw financial data streams?
2. **BitNet Model Execution:** Since BitNet is a probabilistic model, what framework (e.g., ONNX, custom matrix multiplier) will be used to keep memory usage under the 20 MB budget?
3. **Yahoo/Mynet API Keys:** Do we have access to structured API endpoints, or must the system rely entirely on HTML scraping for local values?
