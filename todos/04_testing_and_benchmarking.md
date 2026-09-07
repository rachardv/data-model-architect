# 04 - Testing, Physical Validation & Benchmarking

Focus: Mega-Benchmark Suite, In-Memory DuckDB Validation, Metric Conservation (Zero Chasm Inflation), and Referential Integrity.

---

## Active Tasks & Known Issues

- [x] **25-Domain Enterprise Mega-Benchmark**
  - Full automated evaluation running across 25 diverse domains (Aviation, Healthcare, Banking, Gaming, etc.) in ~1.1 seconds.

- [x] **Official TPC-DI 3-Batch Lifecycle & 46 Automated Audit Queries (`tpcdi_audit.sql`)**
  - Upgraded from 18 synthetic checks to the full official 3-batch sequential lifecycle:
    - Batch 1: Cold start historical bulk load (DimCustomer, DimAccount, DimSecurity, DimCompany, DimBroker, DimDate, DimTime, FactTrade, FactHoldings, FactCashBalances, FactMarketHistory, FactWatches, Prospect).
    - Batch 2: Incremental CDC with SCD2 versioning, position updates, new customer/account inserts, and quarantine isolation.
    - Batch 3: Late-arriving trades and historical restatements verifying Point-in-Time causality to historical profiles.
  - Implemented all 46 automated audit queries covering row counts, metric reconciliation, SCD2 intervals, referential integrity, surrogate key uniqueness, and `DImessages` quarantine logging with 0.0000 metric drift.
  - Full suite verified via `tests/test_tpcdi_full_benchmark.py` and integrated into `IndustryBenchmarkRunner`.

- [x] **Four Physical Post-Generation Pillars**
  - 1. Metric Conservation (exact parity between raw amounts and mart aggregations).
  - 2. Temporal Causality (SCD2 Point-in-Time joins).
  - 3. Referential Integrity (zero duplicate PKs, caught orphan FKs).
  - 4. Query Execution (real hash-join execution in DuckDB).

- [ ] **[Architecture] Comprehensive Model Validation Strategy & Enterprise Risk Profiling Matrix**
  - **Problem:** While the system validates 5 physical pillars in DuckDB, there is no formal, unified Validation Strategy document mapping out every architectural risk category, their business impact, automated pre/post-generation gates, and recovery remediation paths.
  - **The 9 Enterprise Risk Categories to Formally Profile:**
    1. **RSK-01 (Semantic Inversion Trap):** Business user requested live transactional CRUD, but engine compiled an analytical lakehouse (or vice versa), causing database locking and latency bottlenecks.
    2. **RSK-02 (Chasm & Fan-Out Trap):** Multi-fact drill-across joins or 1:N fan-out multiplying revenue, fees, or balances across line items without pre-aggregation CTEs.
    3. **RSK-03 (Temporal Causality Leakage):** Late-arriving dimension records or improper effective date joins attributing historical transactions to incorrect current states (SCD2 timeline bleed).
    4. **RSK-04 (Referential & Deduplication Risk):** Duplicate primary keys slipping through to Gold layer, or unhandled foreign key orphans (-1 sentinel mapping failure).
    5. **RSK-05 (Execution Plan Traps):** Unbounded recursive CTEs in hierarchy closure tables or accidental Cartesian cross-joins causing query timeouts or out-of-memory crashes.
    6. **RSK-06 (Adversarial Skew & Memory Spill):** Extreme key skew (Zipfian 80/20 power-law) causing partition hot-spots or hash-join memory blowout under constrained RAM.
    7. **RSK-07 (Requirement Volatility & Refactoring Debt):** Schema rigidity where evolving business features force costly full schema rebuilds. Mitigated by enforcing Lowest Atomic Grain, Wide Additive Dimensions, Role-Playing Views, and Bronze Raw JSON buffers.
    8. **RSK-08 (Right to be Forgotten & Privacy Erasure):** GDPR Art. 17 / CCPA erasure causing orphan foreign keys or breaking 7-year financial accounting rules. Mitigated by Pseudonymization Sentinels (`'REDACTED'`) and Cryptographic Shredding DDL.
    9. **RSK-09 (Downstream Blast Radius & Contract Drift):** Renaming or altering core mart columns silently breaking downstream dashboards, ML feature stores, and reverse-ETL syncs. Mitigated by Column-Level Lineage checks and Semantic Versioning Views (`v1` on `v2`).
  - **Proposed Solution & Architecture:**
    - **4-Tier Defense-in-Depth:**
      - *Tier 1:* Pre-Generation Intake & Semantic Static Analysis (Vector completeness & contradiction gate).
      - *Tier 2:* SQL AST & Graph Traversal Linter (Anti-Cartesian, CTE pre-aggregation, blast radius linter).
      - *Tier 3:* In-Memory Physical Proof Engine (DuckDB metric conservation, SCD2 point-in-time, GDPR pseudonymization proof).
      - *Tier 4:* Adversarial Chaos & Skew Stress Engine (Zipfian 80/20 key skew, clock drift, 16MB RAM cap spill-to-disk proof).
    - **Deliverable:** Document complete strategy in `docs/VALIDATION_STRATEGY.md` and wire automated `ValidationRiskScorecard` into Captain Orchestrator.
  - **Priority:** High / Critical

- [ ] **[Architecture] Adversarial Chaos & Data Skew Stress Testing Engine**
  - **Problem:** Current benchmark harnesses execute against clean synthetic rows at low scale (`sf=0.01`). Real-world enterprise pipelines fail because of extreme key skew (Zipfian distributions where 20% of orders belong to a single guest checkout key), out-of-order clock drift across distributed nodes, corrupted UTF-8 byte sequences, and high-cardinality null foreign keys. Low-scale tests suffer from an in-memory bias where hash joins fit in CPU cache, masking spill-to-disk crashes that occur at 100M+ rows.
  - **Proposed Architectural Solution:**
    1. **Chaos Ingestion Generator (`AdversarialChaosGenerator`):**
       - *Zipfian Key Skew:* Inject heavily skewed join keys (80/20 power-law distribution) to verify hash-join memory resilience and absence of thread execution bottlenecks.
       - *Clock Drift & Race Conditions:* Randomly jitter event timestamps by $\pm 48$ hours to test SCD2 point-in-time timeline robustness.
       - *Corrupted Payloads:* Inject malformed JSON, invalid UTF-8 sequences, and negative quantities to verify Silver quarantine isolation.
    2. **Spill-to-Disk Memory Cap Harness:** Run DuckDB stress tests with restricted buffer manager memory (`PRAGMA max_memory='16MB'`) to physically prove that generated SQL plans complete external sort/spill-to-disk without throwing out-of-memory errors.
  - **Priority:** High / Critical

- [ ] **Continuous Regression CI Action**
  - **Problem:** Running tests manually via `py -3.14 -m pytest` is fast, but should be enforced via GitHub Actions on every pull request.
  - **Proposed Solution:** Add `.github/workflows/ci.yml` matrix testing across Python 3.11, 3.12, 3.13, and 3.14.
  - **Priority:** Medium

---

## Add New Items Below
