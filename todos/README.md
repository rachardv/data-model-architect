# Data Model Architect - Project TODO & Improvement Tracker

This directory tracks bugs, architectural improvements, and planned enhancements to make the data modeling engine production-ready, intuitive for non-technical business stakeholders, and mathematically resilient.

---

## Tracking Dashboard by Category

| Category | File | Focus Area | Status |
|---|---|---|---|
| **1. Intake & Discovery** | [01_intake_and_interview_engine.md](01_intake_and_interview_engine.md) | NLP parsing, dynamic question generation, 5-vector hard gate | Active |
| **2. Decision Engine** | [02_decision_and_classification.md](02_decision_and_classification.md) | Kimball decision tree, OLTP 3NF branch, Bridge tables | Active |
| **3. Pipeline & Code Gen** | [03_medallion_and_pipeline_codegen.md](03_medallion_and_pipeline_codegen.md) | Bronze/Silver/Gold DDL, dbt project generator, SCD2 merges | Active |
| **4. Testing & Verification** | [04_testing_and_benchmarking.md](04_testing_and_benchmarking.md) | Mega-benchmark, DuckDB in-memory execution, chasm trap tests | Active |
| **5. UX & Developer Tools** | [05_user_experience_and_tooling.md](05_user_experience_and_tooling.md) | Interactive terminal/chat interviewer, ERDs, data contracts | Active |

---

## Status Legend
- [ ] **Backlog**: Identified, waiting for prioritization.
- [-] **In Progress**: Actively being worked on or designed.
- [x] **Completed**: Built, tested, and verified.
- [!] **Critical**: High-priority architectural flaw or bug.

---

## 🎯 Current High-Priority Architectural Focus
1. **Ambiguous Business Truth (Multi-Stakeholder Semantic Conflicts)** — See [01_intake_and_interview_engine.md](01_intake_and_interview_engine.md)
   - Handling conflicting definitions from sales, finance, and product (e.g., *"account active"*).
   - Multi-perspective semantic tagging (`is_active_sales`, `is_active_finance`) and contradiction reconciliation flow.
2. **The Grain Trap (Atomic Enforcement & User Pushback)** — See [01_intake_and_interview_engine.md](01_intake_and_interview_engine.md)
   - Proactive pushback against users requesting premature aggregated fact tables (e.g. *"monthly store revenue"*).
   - Automated 2-tier architecture (lowest atomic fact + materialized gold aggregate mart).
3. **Comprehensive Model Validation Strategy & Risk Matrix** — See [04_testing_and_benchmarking.md](04_testing_and_benchmarking.md)
   - Profiling 6 key failure modes (Semantic Inversion, Chasm Traps, Temporal Leakage, FK Orphans, Cartesian Traps, Contract Drift).
   - Formal deliverable: `docs/VALIDATION_STRATEGY.md` with integrated DuckDB risk scorecard.
4. **Multi-Process Bus Matrix Explosion (Global Conformed Dimension Registry)** — See [02_decision_and_classification.md](02_decision_and_classification.md)
   - Preventing fractured dimensions across multi-department workflows (ordering $\rightarrow$ fulfillment $\rightarrow$ billing $\rightarrow$ refunds).
   - Enforcing identical surrogate key algorithms and canonical schemas across independent compilation passes.

---

## How to Add New Items
Simply open the relevant file in this folder and add a new item under **Backlog** using this format:

`markdown
- [ ] **[Area] Brief Title**
  - **Problem:** What is wrong or missing?
  - **Proposed Solution:** How should the engine handle it?
  - **Priority:** High / Medium / Low
`
