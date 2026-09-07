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

- [ ] **[Architecture] Target Warehouse Dialects & Physical Storage Layout (Partitioning, Clustering & Z-Ordering)**
  - **Problem:** Generated DDL currently emits generic ANSI/DuckDB SQL without physical layout optimizations. In cloud data warehouses (Snowflake, BigQuery, Databricks Delta Lake), multi-million/billion row fact tables without partition pruning and clustering spend excessive compute budget performing full table scans.
  - **Proposed Architectural Solution:**
    1. **Dialect Engine Profile:** Support target dialect profiles (`snowflake`, `bigquery`, `databricks_delta`, `postgres`, `duckdb`).
    2. **Automated Partition & Cluster Inference:**
       - Infer `PARTITION BY DATE(event_timestamp)` or `PARTITION BY RANGE(date_key)` based on the table's primary time grain.
       - Infer `CLUSTER BY (tenant_id, customer_sk)` or Delta/Iceberg `OPTIMIZE ZORDER BY` based on high-frequency dimension foreign keys.
    3. **dbt Config Block Generation:** Auto-inject `{{ config(materialized='incremental', partition_by={...}, cluster_by=[...]) }}` headers into all generated dbt fact models.
  - **Priority:** High / Critical

- [ ] **Automated Data Governance & Dynamic PII Masking Policies**
  - **Problem:** Customer attributes containing sensitive PII (SSN, credit card, phone, email, date of birth) are defined as plain unmasked text without governance tags.
  - **Proposed Architectural Solution:**
    1. **PII Semantic Classifier:** Pattern-match common sensitive attributes during column generation and assign governance tags (`pii_type: email|ssn|phone|financial`).
    2. **Dynamic Masking DDL Generation:** Generate dialect-specific security policies:
       - Snowflake: `CREATE MASKING POLICY pii_email_mask AS (val string) -> CASE WHEN current_role() IN ('ANALYST_PII') THEN val ELSE regexp_replace(val, '.+@', '****@') END`.
       - BigQuery: Auto-attach policy tag taxonomy URIs (`data_governance_tags: taxonomy/pii_restricted`).
    3. **OpenLineage & Catalog Integration:** Export column-level lineage and classification tags to OpenLineage JSON for ingestion into DataHub, Collibra, or Alation.
  - **Priority:** High

---

## Add New Items Below
