# 03 - Medallion Architecture & Pipeline Code Generation

Focus: Bronze Layer (Raw Storage), Silver Layer (Deduplication & Quarantine), Gold Layer (SCD2 Merges & Fact Load), and dbt Project Exports.

---

## Active Tasks & Known Issues

- [x] **End-to-End Medallion Pipeline in DuckDB**
  - Fully verified Bronze landing views, Silver deduplication/quarantine views, and Gold SCD2 merges executing in in-memory DuckDB.

- [x] **dbt Project Evaluator & Project Exporter**
  - Automatically exports `dbt_project.yml`, staging models, marts models, and schema YAML tests.

- [ ] **Automated Quarantine Error-Routing Policies in Silver Layer**
  - **Problem:** Silver layer quarantine views currently capture null PKs or orphan FKs, but do not attach explicit error-code tags (*E001_NULL_PK*, *E002_ORPHAN_FK*) to quarantined rows.
  - **Proposed Solution:** Add an `ingestion_error_code` and `quarantined_at` timestamp column to all silver quarantine CTEs for production observability.
  - **Priority:** Medium

- [ ] **Incremental dbt Materialization for Gold Facts**
  - **Problem:** dbt fact models currently generate as standard table materializations (`table`).
  - **Proposed Solution:** Allow opting into `materialized='incremental'` with `unique_key` and `is_incremental()` Jinja blocks for high-volume enterprise tables.
  - **Priority:** Medium

- [ ] **Data Contract YAML Export (Great Expectations / OpenDataContract)**
  - **Problem:** The engine compiles contracts internally, but exporting to OpenDataContract standard YAML format will improve compatibility with enterprise data catalogs.
  - **Proposed Solution:** Add `export_open_data_contract_yaml()` to `DataContractCompiler`.
  - **Priority:** Low

---

## Add New Items Below
