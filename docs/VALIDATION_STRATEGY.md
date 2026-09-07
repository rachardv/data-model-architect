# Enterprise Data Model Validation Strategy & Risk Profiling Matrix

This document defines the formal, unified **Validation Strategy & Risk Profiling Architecture** for `data-model-architect`. It establishes how data models are deterministically validated against 9 critical enterprise failure modes across a 4-tier defense-in-depth pipeline before deployment.

---

## 1. Architectural Philosophy: The Mathematical Invariants of Modeling

In mature data engineering, a data model cannot simply be generated and trusted based on syntax alone. Every production model must adhere to the physical laws of dimensional modeling:

1. **The Law of Metric Conservation ($\sum 	ext{Raw} \equiv \sum 	ext{Mart}$)**:
   Aggregating transactional facts across conformed dimensions must reconcile to the source penny ($0.0000$ drift). Cartesian cross-joins or multi-fact fan-out traps that multiply revenue are unacceptable.
2. **The Law of Temporal Causality (Point-in-Time Invariant)**:
   An event that occurred on `2026-01-10` must strictly bind to the dimension state valid on that date, even if the customer updated their profile on `2026-01-15`.
3. **The Law of Referential & Grain Integrity**:
   Every foreign key must resolve to a valid dimension key; unhandled orphans or duplicate natural keys are quarantined at the Silver layer.
4. **The Law of Adaptability (Schema Rigidity Prevention)**:
   A base fact table must always be preserved at its lowest atomic grain, allowing the business to ask new questions without destructive backfills or pipeline teardowns.
5. **The Law of Privacy & Regulatory Compliance (GDPR Art. 17)**:
   Erasing personal identity under the Right to be Forgotten must never corrupt financial sums or create orphan foreign keys in historical transaction ledgers.

---

## 2. The 4-Tier Defense-in-Depth Pipeline

```
[User Request / Narrative]
         │
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: Pre-Flight Intake & Semantics (Static Text)                    │
│ • RSK-01: Workload Intent Hard Gate (OLTP vs OLAP Mismatch)            │
│ • RSK-07: Atomic Grain Enforcement & Adaptability Pushback             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 2: SQL AST, Lineage & Graph Traversal Linter (Syntax Graph)       │
│ • RSK-02: Strict Mart Separation & Anti-Cartesian Join Linter          │
│ • RSK-05: Recursive Hierarchy Cycle & Unbounded Loop Detector          │
│ • RSK-08: PII Pattern Classifier & Dynamic Masking Policy Linter       │
│ • RSK-09: Column-Level Lineage Blast Radius & Versioning View Linter   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 3: In-Memory Physical Proofs (DuckDB Runtime Execution)           │
│ • RSK-02: Metric Conservation Proof (Raw == Mart to $0.0000)           │
│ • RSK-03: SCD2 Point-in-Time Causality & Sentinel Proof (9999-12-31)   │
│ • RSK-04: Referential Integrity & Silver Quarantine Isolation Proof    │
│ • RSK-05: Physical Hash-Join EXPLAIN Execution Plan (<100ms)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 4: Adversarial Stress & Compliance Proofs (Hardware & Edge Cases) │
│ • RSK-06: Zipfian 80/20 Key Skew under 16MB RAM Cap (Spill-to-Disk)   │
│ • RSK-08: GDPR Pseudonymization Sentinel Proof (Zero-Orphan Erasure)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
                       [ValidationRiskScorecard]
            CERTIFIED_PRODUCTION_READY  vs  CRITICAL_HALT
```

---

## 3. The 9 Enterprise Risk Profiles

### RSK-01: Semantic Inversion Trap
* **Root Cause:** User requested low-latency transactional CRUD (OLTP), but the compiler generated an analytical Star Mart lakehouse (or vice versa).
* **Impact:** Severe database locking, latency spikes, or broken application state.
* **Mitigation:** **Tier 1 5-Vector Completeness Gate** halts execution if workload intent contradicts the chosen physical schema pattern.

### RSK-02: Chasm & Fan-Out Trap (Metric Inflation)
* **Root Cause:** Joining multiple 1:N child tables (e.g. `order_items` and `order_payments`) to a shared parent (`orders`) causes Cartesian row multiplication.
* **Impact:** Revenue and payment sums are multiplied by $2	imes - 10	imes$ on executive dashboards.
* **Mitigation:** 
  1. **Strict Mart Separation (Tier 2):** Disallow direct cross-fact joins between tables of disparate grains in a single mart query.
  2. **Metric Conservation Proof (Tier 3):** Physical DuckDB assertion proving $\sum 	ext{Raw} \equiv \sum 	ext{Mart}$ down to $0.0000$ drift.

### RSK-03: Temporal Causality Leakage (Timeline Bleed)
* **Root Cause:** Late-arriving events join to current active dimension rows (`is_current = TRUE`) rather than historical effective intervals.
* **Impact:** Historical sales misattributed to current customer addresses or updated loyalty tiers.
* **Mitigation:** **Tier 3 Physical Proof** verifying strictly closed SCD2 intervals (`EndDate == Next EffectiveDate`), `9999-12-31` high-water sentinels, and Point-in-Time join assertions.

### RSK-04: Referential Orphan & Deduplication Failure
* **Root Cause:** Unmatched foreign keys or duplicate natural keys slip through without quarantine routing.
* **Impact:** Missing sales in inner joins, inflated row counts, and untraceable records.
* **Mitigation:** **Tier 3 Silver Quarantine Proof** ensuring dirty rows route to `DImessages` / reject CTEs and zero foreign key orphans reach Gold marts.

### RSK-05: Execution Plan Traps & Circular Loops
* **Root Cause:** Missing join predicates creating accidental Cartesian cross-products, or infinite loops in parent-child hierarchy trees.
* **Impact:** Query timeouts, out-of-memory crashes on cloud warehouses, massive compute costs.
* **Mitigation:** **Tier 2 AST Linter** verifying explicit join predicates + **Tier 3 DuckDB EXPLAIN** plan inspection ensuring sub-100ms hash joins.

### RSK-06: Adversarial Skew & Memory Spill Failure
* **Root Cause:** Extreme key skew (Zipfian 80/20 power-law) causes partition hot-spots and hash-join memory blowouts on distributed nodes.
* **Impact:** Spark/Snowflake node OOM crashes on multi-million row loads.
* **Mitigation:** **Tier 4 Adversarial Chaos Generator** executing Zipfian skewed keys under a restricted `16MB` DuckDB RAM cap. Passes for memory stability (no crash) and emits physical cluster key advice if disk spill occurs.

### RSK-07: Requirement Volatility & Refactoring Debt
* **Root Cause:** Rapidly evolving business requirements break tightly coupled, prematurely aggregated models.
* **Impact:** Costly petabyte-scale backfills, broken dashboards, and slow engineering velocity.
* **Mitigation:**
  - **Lowest Atomic Grain:** Preserving base transaction/event facts so unexpected slicing requires zero schema teardown.
  - **Wide Additive Dimensions:** Dimensions absorb new descriptive attributes as nullable columns without touching facts.
  - **Bronze Raw JSON Buffer:** Storing `payload_raw JSON` allows mining historical attributes without upstream API changes.
  - **Role-Playing Views:** Reusing conformed dimensions (e.g. `dim_date`) via views (`v_shipped_date`, `v_delivery_date`).

### RSK-08: Right to be Forgotten & Privacy Erasure (GDPR Art. 17 / CCPA)
* **Root Cause:** Deleting a customer row under GDPR creates orphan foreign keys in historical facts, or deleting facts violates 7-year SOX tax accounting laws.
* **Impact:** Fines up to €20M / 4% global turnover OR broken financial reconciliation.
* **Mitigation:**
  - **Pseudonymization Sentinels:** Customer PII is updated to `'REDACTED'`, phone to `NULL`, and email to a salt hash. The surrogate key (`customer_sk`) is preserved.
  - **Zero Orphan Fact Proof:** Fact tables retain 100% of rows and sums with zero orphan keys, satisfying both privacy and financial compliance.

### RSK-09: Downstream Blast Radius & Breaking Changes
* **Root Cause:** Modifying a core mart column breaks downstream BI dashboards, ML feature stores, and reverse-ETL feeds.
* **Impact:** Production outages for downstream data consumers.
* **Mitigation:** **Column-Level Lineage Linter** + **Semantic Versioning Views** (`fct_orders_v1` as a backward-compatible view on top of `v2`).

---

## 4. The Extensible Plugin Registry (`@register_risk`)

To add a new risk evaluator (e.g. `RSK-10: FinOps Unpartitioned Scan Hazard`):
1. Inherit from `BaseRiskEvaluator`.
2. Decorate with `@register_risk`.
3. Implement `evaluate(context: ValidationContext) -> RiskResult`.

The core `ValidationStrategyEngine` automatically discovers and executes the rule in deterministic sequence.

### Error Handling Policy:
- **CRITICAL / HIGH Evaluators:** Unhandled runtime exceptions trigger an immediate compile-time `CRITICAL_HALT`.
- **MEDIUM / LOW Evaluators:** Unhandled exceptions are quarantined as `EVALUATOR_ERROR` in the scorecard while compilation proceeds.
