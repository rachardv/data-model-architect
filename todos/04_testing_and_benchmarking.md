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
