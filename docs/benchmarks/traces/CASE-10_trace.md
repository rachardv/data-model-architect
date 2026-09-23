# Decision Trace Report: CASE-10 — Retail Banking Semi-Additive Balances, Factless Events & Rollup Navigation

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `3201.42ms`
> **Timestamp (UTC):** `2026-09-23T21:19:41.917905+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `retail_banking`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Ralph Kimball & Margy Ross (2013), "The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling" (3rd Edition), Chapter 7 ("Financial Services: Periodic Snapshot Fact Tables, Semi-Additive Metrics & Factless Facts"), pp. 241-274, and Chapter 19 ("Aggregate Navigation and Materialized Summary Tables"), pp. 493-512.
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
We operate an enterprise retail banking platform managing retail checking and savings accounts across national branch networks. Every night, a nightly snapshot captures account ending balances and available balances; these metrics are strictly semi-additive (additive across accounts, customers, and branches, but strictly non-additive across time, requiring point-in-time closing balance reductions). Additionally, security authentication and fraud monitoring requires tracking customer security events (logins, password resets, MFA challenges) as a pure factless fact table with zero numeric measures, where the grain is defined solely by the composite dimension foreign keys. To accelerate high-throughput executive branch dashboards without scanning multi-billion row daily snapshots, the warehouse maintains a companion monthly branch rollup aggregate table with navigation routing that mathematically reconciles with base fact closing balances.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `FACTLESS_FACT_COVERAGE`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `dim_retail_banking_attendee` | `DIMENSION` | `attendee_sk` | 3 |
| `dim_retail_banking_event` | `DIMENSION` | `event_sk` | 3 |
| `fact_retail_banking_attendance_coverage` | `FACTLESS_FACT` | `attendee_sk, event_sk, date_sk` | 3 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Semi-Additive Point-in-Time Monthly Closing Balance | `scalar_eq` | `3300.0` | `3300.0` | `1.77ms` | ✅ PASS |
| Cross-Sectional Dimensional Additivity | `scalar_eq` | `8800.0` | `8800.0` | `0.39ms` | ✅ PASS |
| Factless Security Event Exact Occurrence Count | `scalar_eq` | `2` | `2` | `0.57ms` | ✅ PASS |
| Aggregate Rollup Parity Against Base Fact Closing Balance | `scalar_eq` | `8800.0` | `8800.0` | `0.38ms` | ✅ PASS |
| Non-Additive Derived Ratio Component Derivation | `scalar_eq` | `1650.0` | `1650.0` | `0.42ms` | ✅ PASS |

### Query Details
#### Query 1: Semi-Additive Point-in-Time Monthly Closing Balance
```sql
WITH ranked_balances AS (
  SELECT 
    b.branch_sk,
    f.account_sk,
    f.ending_balance,
    ROW_NUMBER() OVER (
      PARTITION BY f.account_sk 
      ORDER BY d.calendar_date DESC
    ) AS rn
  FROM fact_daily_account_balances f
  JOIN dim_retail_banking_branch_core b ON f.branch_sk = b.branch_sk
  JOIN dim_date d ON f.snapshot_date_key = d.date_sk
  WHERE d.calendar_year = 2026 AND d.calendar_month = 1
) SELECT CAST(ROUND(SUM(ending_balance), 2) AS DOUBLE) FROM ranked_balances WHERE rn = 1 AND branch_sk = 'BR-DOWNTOWN';

```
#### Query 2: Cross-Sectional Dimensional Additivity
```sql
SELECT CAST(ROUND(SUM(ending_balance), 2) AS DOUBLE) FROM fact_daily_account_balances WHERE snapshot_date_key = 20260131;

```
#### Query 3: Factless Security Event Exact Occurrence Count
```sql
SELECT COUNT(*) FROM fact_customer_security_events e JOIN dim_retail_banking_customer_core c ON e.customer_sk = c.customer_sk WHERE c.customer_id = 'C-1001';

```
#### Query 4: Aggregate Rollup Parity Against Base Fact Closing Balance
```sql
SELECT CAST(ROUND(SUM(total_closing_balance), 2) AS DOUBLE) FROM agg_monthly_branch_balances WHERE calendar_year = 2026 AND calendar_month = 1;

```
#### Query 5: Non-Additive Derived Ratio Component Derivation
```sql
SELECT CAST(ROUND(total_closing_balance / total_accounts_count, 2) AS DOUBLE) FROM agg_monthly_branch_balances WHERE calendar_year = 2026 AND calendar_month = 1 AND branch_sk = 'BR-DOWNTOWN';

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*