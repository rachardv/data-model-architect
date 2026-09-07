# 04 - Testing, Physical Validation & Benchmarking

Focus: Mega-Benchmark Suite, In-Memory DuckDB Validation, Metric Conservation (Zero Chasm Inflation), and Referential Integrity.

---

## Active Tasks & Known Issues

- [x] **25-Domain Enterprise Mega-Benchmark**
  - Full automated evaluation running across 25 diverse domains (Aviation, Healthcare, Banking, Gaming, etc.) in ~1.1 seconds.

- [x] **Four Physical Post-Generation Pillars**
  - 1. Metric Conservation (exact parity between raw amounts and mart aggregations).
  - 2. Temporal Causality (SCD2 Point-in-Time joins).
  - 3. Referential Integrity (zero duplicate PKs, caught orphan FKs).
  - 4. Query Execution (real hash-join execution in DuckDB).

- [ ] **[Architecture] Comprehensive Model Validation Strategy & Risk Profiling Matrix**
  - **Problem:** While the system validates 5 physical pillars in DuckDB, there is no formal, unified Validation Strategy document mapping out every architectural risk category, their business impact, automated pre/post-generation gates, and recovery remediation paths.
  - **Risk Categories to Formally Profile:**
    1. **Semantic Inversion Risk (Wrong Paradigm Built):** Business user requested live transactional CRUD, but engine compiled an analytical lakehouse (or vice versa), leading to severe database locking and latency bottlenecks.
    2. **Chasm & Fan-Out Trap Risk (Metric Distortion):** Multi-fact drill-across joins or 1:N fan-out multiplying revenue, fees, or balances across line items without pre-aggregation CTEs.
    3. **Temporal Leakage Risk (Point-in-Time Corruption):** Late-arriving dimension records or improper effective date joins attributing historical transactions to incorrect current states (SCD2 timeline bleed).
    4. **Referential & Deduplication Risk:** Duplicate primary keys slipping through to Gold layer, or unhandled foreign key orphans (-1 sentinel mapping failure).
    5. **Execution Plan Traps:** Unbounded recursive CTEs in hierarchy closure tables or accidental Cartesian cross-joins causing query timeouts or out-of-memory crashes.
    6. **Schema Evolution & Silent Contract Drift:** Upstream schema changes breaking downstream marts without automated silver-layer quarantine routing.
  - **Proposed Solution & Architecture:**
    - **Pre-Generation Gates:** Strict 100% Vector Completeness hard-gate, Semantic Sanity gibberish filter, and Contradiction detection.
    - **AST & Code Gen Linter:** Pre-execution SQL AST audit verifying absence of cartesian products and enforcing CTE pre-aggregation on multi-fact queries.
    - **Physical In-Memory Validation:** DuckDB 5-pillar execution harness proving metric conservation ($\sum \text{Raw} == \sum \text{Mart}$), temporal causality, referential integrity, and query execution.
    - **Adversarial Chaos Ingestion:** Injecting high-skew, late-arriving timestamps, and null keys to verify quarantine resilience.
    - **Deliverable:** Document complete strategy in `docs/VALIDATION_STRATEGY.md` and wire automated risk scorecard into Captain Orchestrator.
  - **Priority:** High / Critical

- [ ] **Automated Stress Testing with Synthetic Skew Data**
  - **Problem:** Mega-benchmark uses clean synthetic rows. Real-world data has high-cardinality nulls, extreme key skew, and out-of-order event timestamps.
  - **Proposed Solution:** Add an adversarial synthetic data generator that injects out-of-order records, late-arriving data, and null foreign keys to test pipeline self-healing.
  - **Priority:** Medium

- [ ] **Continuous Regression CI Action**
  - **Problem:** Running tests manually via `py -3.14 -m pytest` is fast, but should be enforced via GitHub Actions on every pull request.
  - **Proposed Solution:** Add `.github/workflows/ci.yml` matrix testing across Python 3.11, 3.12, 3.13, and 3.14.
  - **Priority:** Medium

---

## Add New Items Below
