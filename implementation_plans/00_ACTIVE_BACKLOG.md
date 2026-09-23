# Active Implementation Backlog & Deferred Initiatives

This document logs active tasks, future phases, and deferred features per the **Zero-Lost Bugs & Features Invariant** of the engineering protocol.

---

## ✅ Completed Phases

### 1. Phase 2: Golden Snapshot & Regression Diffing Engine
* **Status:** `COMPLETED`
* **Artifacts:**
  * Engine: `src/snapshot_engine.py` (`GoldenSnapshotEngine`)
  * Golden Snapshot: `benchmarks/baselines/golden_snapshot.json` (8 curated Kimball baseline & trap cases)
  * CLI Flags: `--snapshot`, `--diff`, `--strict-drift`, `--baseline-path`, `--latency-threshold`
  * Tests: `tests/test_snapshot_engine.py` (8 unit tests passing)
  * Capabilities: Schema drift detection (tables, columns, PKs), status/verdict flip detection, query assertion flip detection, query latency regression alerting (> 100% and >= 1.0ms delta).

---

## ⏳ Deferred Phases (Saved for Later Execution per User Directive)

### 2. Phase 3: Synthetic AI Fuzzing & Scale Generator
* **Status:** `DEFERRED / BACKLOGGED`
* **Target Milestone:** Post-Phase 2
* **Objective:**
  * Build synthetic case generator in `benchmarks/catalog/synthetic/`.
  * Generate 50+ varied industry narratives (AdTech, Logistics, Gaming, Clinical Trials) using structured LLM prompts.
  * Fuzz Gate 0 Intake Engine with ambiguous, incomplete, and adversarial business stories.
  * Ensure AI-generated cases only graduate to benchmark status if verified against DuckDB physical assertions.

---

### 3. Critique #5: Semantic Metric Ambiguity & Conflicting Multi-Stakeholder Truth (FAANG Senior Review)
* **Status:** `DEFERRED / ARCHIVED FOR LATER` (per user directive 2026-09-23)
* **Priority:** Tier 2 (High-Impact Correctness & Governance)
* **Affected Components:**
  * `src/noun_verb_parser.py` (Multi-stakeholder metric intent extraction)
  * `src/schema_author.py` (Perspective-aware conformed dimension column aliasing & 64-bit BigInt hashing)
  * `src/dbt_generator.py` (dbt Semantic Layer `models/metrics.yml` compilation)
  * `forge/risk_engine.py` (`RSK-15` Semantic Metric Ambiguity Linter)
  * `forge/risk_dispatcher.py` (Battery M: Multi-Perspective SQL Parity Battery)
  * `benchmarks/catalog/curated/` (`CASE-11` Multi-Stakeholder SaaS Subscription Benchmark)
* **Blast Radius Risk:**
  * **Metric Collision ("War of Metrics"):** Different departments (Sales vs. Product vs. Finance) defining the same concept (e.g. *"Active Customer"*) incompatibly, causing conflicting figures in board presentations.
  * **Dimension Fragmentation Trap:** Teams creating duplicate disconnected dimensions (`dim_sales_customer`, `dim_finance_customer`) that destroy Kimball conformed cross-functional reporting.
  * **32-Character String Key Bottleneck:** Joining multi-billion row facts on MD5/UUID string surrogate keys instead of hardware-optimized 64-bit integers (`FARM_FINGERPRINT` / `xxHash64`).
* **Planned Architectural Remediation:**
  1. **Perspective-Aware Conformed Attributes:** Retain a single conformed dimension (`dim_customer_core`) with explicit perspective attributes: `is_active_sales_contract`, `is_active_product_user`, `is_active_finance_billed`.
  2. **dbt Semantic Layer Spec:** Compile `models/metrics.yml` with formal certified metric formulas, grains, and department owners.
  3. **64-bit BigInt Hashing:** Standardize surrogate key compilation on `FARM_FINGERPRINT(...)` / `xxhash64(...)`.
  4. **Risk Linter `RSK-15` & Case `CASE-11`:** Audit and certify multi-perspective metrics in DuckDB.

