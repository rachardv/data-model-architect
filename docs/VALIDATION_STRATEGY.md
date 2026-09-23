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

## 2. The 3-Layer Defense-in-Depth Validation Hierarchy

The validation architecture operates across **3 distinct, non-redundant layers**:

1. **Layer 1: Pre-Flight Intake Gate (Gate 0)**
   - Audits the unstructured business narrative before any code is generated.
   - Evaluates the 5 Information Vectors (Workload Intent, Entity Grain, Temporal Policy, Lifecycle Funnel, Multiplicity).
   - Traps self-contradictory requirements (e.g. sub-millisecond ACID OLTP write throughput vs 10B cold columnar parquet scans).

2. **Layer 2: Model Dual-Gate (Static Blueprints & Physical Execution)**
   - **2A. Static Reviewer Gates:** Audits schema AST, foreign key dependency graphs (DFS cycle detection), chasm trap fanout risks, and PII masking.
   - **2B. Physical In-Memory Proofs:** Boots DuckDB, seeds test data, and mathematically proves metric conservation ($0.0000 variance), SCD2 point-in-time joins, and hash-join execution plans.

3. **Layer 3: System-Level Predefined Benchmark Gate (The Certification Battery)**
   - Evaluates curated enterprise cases **1-by-1 sequentially** in isolated DuckDB databases.
   - Declaratively loaded from `benchmarks/catalog/curated/` with explicit academic and textbook citations.
   - Specifically tests that **intentional traps** (cyclic graphs, contradiction prompts, chasm traps) trigger defense halts.
   - Executes domain-specific physical SQL verification queries against generated tables.
   - Audits all decisions into `docs/benchmarks/traces/<case_id>_trace.json` and `.md`, with clean overwrite semantics upon redeployment.

#### The 8 Curated Textbook Benchmark Cases:
| Case ID | Domain | Name | Hazard Category | Trap? | Source & Provenance Citation |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `CASE-01` | `retail` | Enterprise Retail Kimball Star Mart | `CLEAN_BASELINE` | No | Ralph Kimball, *Data Warehouse Toolkit* (3rd Ed), Ch 2: Retail Sales |
| `CASE-02` | `healthcare` | Healthcare Encounter & Diagnosis Bridge | `BRIDGE_CO_OWNERSHIP` | No | Ralph Kimball, *Data Warehouse Toolkit* (3rd Ed), Ch 10: Healthcare Bridge |
| `CASE-03` | `banking` | Banking Multi-Owner Joint Account Co-Ownership | `BRIDGE_CO_OWNERSHIP` | No | Ralph Kimball, *Data Warehouse Toolkit* (3rd Ed), Ch 11: Financial Services |
| `CASE-04` | `inventory` | Retail Inventory Periodic Daily Snapshot | `CLEAN_BASELINE` | No | Ralph Kimball, *Data Warehouse Toolkit* (3rd Ed), Ch 3: Inventory Snapshot |
| `TRAP-01` | `highfreq` | Contradiction Guardrail Trap | `CONTRADICTION_HALT` | Yes | E.F. Codd & Christopher Adamson, *Star Schema*, Ch 1: OLTP vs OLAP |
| `TRAP-02` | `sales_fulfillment` | Multi-Fact Chasm Trap Fanout | `CHASM_TRAP_FANOUT` | Yes | Christopher Adamson, *Star Schema*, Ch 12: Disparate Grains & Chasm Traps |
| `TRAP-03` | `organization` | Cyclic Foreign Key Dependency Loop | `CYCLIC_FK_GRAPH` | Yes | E.F. Codd & Bill Inmon, *Building the Data Warehouse*: Recursive Loops |
| `TRAP-04` | `telecom` | SCD2 Historical Amnesia Point-in-Time Trap | `SCD2_HISTORICAL_AMNESIA` | Yes | Ralph Kimball, *Data Warehouse Toolkit* (3rd Ed), Ch 6: Late-Arriving Facts |

---

## 3. The 4-Tier Defense-in-Depth Pipeline

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
│ • RSK-06: Workload Efficiency & Join Fan-Out Factor (<= 1.0000)        │
│ • RSK-08: GDPR Pseudonymization Sentinel Proof (Zero-Orphan Erasure)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
                       [ValidationRiskScorecard]
            CERTIFIED_PRODUCTION_READY  vs  CRITICAL_HALT
```

---

## 4. The 9 Enterprise Risk Profiles & Process Ownership

> [!NOTE]
> For the comprehensive **Anti-Bloat Risk Taxonomy & Intake Decision Matrix**, see [`docs/RISK_TAXONOMY.md`](file:///C:/Coding/VSCode/data-model-architect/docs/RISK_TAXONOMY.md). Every risk profile is owned by a single primary Forge process (A, B, C, or D) to prevent duplicate test coverage and bloat.

### RSK-01: Semantic Inversion Trap
* **Owning Process:** **Process A** (Curated Benchmarks / Intentional Traps) & **Process B** (Static Sensor)
* **Risk Category:** Category 1 (Domain Coverage) & Category 2 (Structural Defect)
* **Root Cause:** User requested low-latency transactional CRUD (OLTP), but the compiler generated an analytical Star Mart lakehouse (or vice versa).
* **Impact:** Severe database locking, latency spikes, or broken application state.
* **Mitigation:** **Tier 1 5-Vector Completeness Gate** halts execution if workload intent contradicts the chosen physical schema pattern (`TRAP-01`).

### RSK-02: Chasm & Fan-Out Trap (Metric Inflation)
* **Owning Process:** **Process B** (Structural Detector) & **Process D** (Universal Invariant Probe)
* **Risk Category:** Category 2 (Structural Defect) & Category 4 (Universal Invariant)
* **Root Cause:** Joining multiple 1:N child tables (e.g. `order_items` and `order_payments`) to a shared parent (`orders`) causes Cartesian row multiplication.
* **Impact:** Revenue and payment sums are multiplied by $2\times - 10\times$ on executive dashboards.
* **Mitigation:** 
  1. **Strict Mart Separation (Process B):** Disallow direct cross-fact joins between tables of disparate grains in a single mart query.
  2. **Metric Conservation Proof (Process D):** Universal physical DuckDB assertion proving $\sum \text{Raw} \equiv \sum \text{Mart}$ down to $0.0000$ drift.

### RSK-03: Temporal Causality Leakage (Timeline Bleed)
* **Owning Process:** **Process D** (Universal Invariant Probe)
* **Risk Category:** Category 4 (Universal Invariant)
* **Root Cause:** Late-arriving events join to current active dimension rows (`is_current = TRUE`) rather than historical effective intervals.
* **Impact:** Historical sales misattributed to current customer addresses or updated loyalty tiers.
* **Mitigation:** **Process D Universal Proof** verifying strictly closed SCD2 intervals (`EndDate == Next EffectiveDate`), `9999-12-31` high-water sentinels, and Point-in-Time join assertions (`TRAP-04`).

### RSK-04: Referential Orphan & Deduplication Failure
* **Owning Process:** **Process D** (Universal Invariant Probe)
* **Risk Category:** Category 4 (Universal Invariant)
* **Root Cause:** Unmatched foreign keys or duplicate natural keys slip through without quarantine routing.
* **Impact:** Missing sales in inner joins, inflated row counts, and untraceable records.
* **Mitigation:** **Process D Silver Quarantine Proof** ensuring dirty rows route to `DImessages` / reject CTEs and zero foreign key orphans reach Gold marts.

### RSK-05: Execution Plan Traps & Circular Loops
* **Owning Process:** **Process B** (Structural Detector) & **Process D** (Universal Invariant Probe)
* **Risk Category:** Category 2 (Structural Defect) & Category 4 (Universal Invariant)
* **Root Cause:** Missing join predicates creating accidental Cartesian cross-products, or infinite loops in parent-child hierarchy trees.
* **Impact:** Query timeouts, out-of-memory crashes on cloud warehouses, massive compute costs.
* **Mitigation:** **Process B AST Linter** verifying explicit join predicates and cycle detection (`TRAP-03`) + **Process D DuckDB EXPLAIN** plan inspection ensuring sub-100ms hash joins.

### RSK-06: Workload Efficiency & Join Fan-Out Stability
* **Owning Process:** **Process C** (Computational Stress Battery)
* **Risk Category:** Category 3 (Computational & Hardware Stress)
* **Root Cause:** Extreme key skew (Zipfian 80/20 power-law) or unoptimized joins cause intermediate Cartesian row multiplication and distributed shuffle blowouts.
* **Impact:** Spark/Snowflake node OOM crashes on multi-million row loads and massive compute bills.
* **Mitigation:** **Process C Workload Fan-Out Battery** executing Zipfian skewed keys on actual synthesized facts and dimensions. Mathematically proves that the join fan-out factor remains $\le 1.0000$ (zero row multiplication) and completes within sub-second SLA.

### RSK-07: Requirement Volatility & Refactoring Debt
* **Owning Process:** **Process A** (Curated Benchmarks)
* **Risk Category:** Category 1 (Domain Coverage)
* **Root Cause:** Rapidly evolving business requirements break tightly coupled, prematurely aggregated models.
* **Impact:** Costly petabyte-scale backfills, broken dashboards, and slow engineering velocity.
* **Mitigation:**
  - **Lowest Atomic Grain:** Preserving base transaction/event facts so unexpected slicing requires zero schema teardown.
  - **Wide Additive Dimensions:** Dimensions absorb new descriptive attributes as nullable columns without touching facts.
  - **Bronze Raw JSON Buffer:** Storing `payload_raw JSON` allows mining historical attributes without upstream API changes.
  - **Role-Playing Views:** Reusing conformed dimensions (e.g. `dim_date`) via views (`v_shipped_date`, `v_delivery_date`).

### RSK-08: Right to be Forgotten & Privacy Erasure (GDPR Art. 17 / CCPA)
* **Owning Process:** **Process B** (Structural Sensor) & **Process C** (Computational Stress Battery)
* **Risk Category:** Category 2 (Structural Defect) & Category 3 (Computational Stress)
* **Root Cause:** Deleting a customer row under GDPR creates orphan foreign keys in historical facts, or deleting facts violates 7-year SOX tax accounting laws.
* **Impact:** Fines up to €20M / 4% global turnover OR broken financial reconciliation.
* **Mitigation:**
  - **Process B Pseudonymization Sentinels:** Customer PII is flagged and updated to `'REDACTED'`, phone to `NULL`, and email to a salt hash. The surrogate key (`customer_sk`) is preserved.
  - **Process C Zero Orphan Fact Proof:** Fact tables retain 100% of rows and sums with zero orphan keys, satisfying both privacy and financial compliance.

### RSK-09: Downstream Blast Radius & Breaking Changes
* **Owning Process:** **Process B** (Structural Sensor)
* **Risk Category:** Category 2 (Structural Defect)
* **Root Cause:** Modifying a core mart column breaks downstream BI dashboards, ML feature stores, and reverse-ETL feeds.
* **Impact:** Production outages for downstream data consumers.
* **Mitigation:** **Process B Column-Level Lineage Linter** + **Semantic Versioning Views** (`fct_orders_v1` as a backward-compatible view on top of `v2`).

---

## 5. The Extensible Plugin Registry (`@register_risk`)

To add a new risk evaluator (e.g. `RSK-10: FinOps Unpartitioned Scan Hazard`):
1. Inherit from `BaseRiskEvaluator`.
2. Decorate with `@register_risk`.
3. Implement `evaluate(context: ValidationContext) -> RiskResult`.

The core `ValidationStrategyEngine` automatically discovers and executes the rule in deterministic sequence.

### Error Handling Policy:
- **CRITICAL / HIGH Evaluators:** Unhandled runtime exceptions trigger an immediate compile-time `CRITICAL_HALT`.
- **MEDIUM / LOW Evaluators:** Unhandled exceptions are quarantined as `EVALUATOR_ERROR` in the scorecard while compilation proceeds.
