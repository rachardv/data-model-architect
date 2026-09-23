# Active Implementation Backlog & Deferred Initiatives

This document logs active tasks, future phases, and deferred features per the **Zero-Lost Bugs & Features Invariant** of the engineering protocol.

---

## ⏳ Deferred Phases (Saved for Later Execution per User Directive)

### 1. Phase 2: Golden Snapshot & Regression Diffing Engine
* **Status:** `DEFERRED / BACKLOGGED`
* **Target Milestone:** Post-Phase 1 Expansion
* **Objective:**
  * Implement baseline snapshot capture to `benchmarks/baselines/golden_snapshot.json`.
  * Track schema table definitions, column types, reviewer scores, and verification query latency metrics.
  * On subsequent harness runs, compute diff vectors (+/- score, schema drift, latency regression).
  * Add `--diff-baseline` CLI flag.

### 2. Phase 3: Synthetic AI Fuzzing & Scale Generator
* **Status:** `DEFERRED / BACKLOGGED`
* **Target Milestone:** Post-Phase 2
* **Objective:**
  * Build synthetic case generator in `benchmarks/catalog/synthetic/`.
  * Generate 50+ varied industry narratives (AdTech, Logistics, Gaming, Clinical Trials) using structured LLM prompts.
  * Fuzz Gate 0 Intake Engine with ambiguous, incomplete, and adversarial business stories.
  * Ensure AI-generated cases only graduate to benchmark status if verified against DuckDB physical assertions.
