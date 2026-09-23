# Decision Trace Report: CASE-12 — Multi-Currency Global Procurement Spot Rate Triangulation

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `90.81ms`
> **Timestamp (UTC):** `2026-09-23T20:42:17.669453+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `global_procurement`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Ralph Kimball & Margy Ross (2013), "The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling" (3rd Edition), Chapter 8 ("Procurement & Global Logistics: Multi-Currency Fact Tables, Daily Spot Rates & Corporate Reporting Currency Triangulation"), pp. 275-304.
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
We operate an international supply chain and manufacturing enterprise procuring components from global suppliers across Europe, Japan, and the Americas. Purchase orders are negotiated and transacted in distinct local currencies (EUR, GBP, JPY), while corporate headquarters requires consolidated financial reporting in US Dollars (USD). Per Kimball Chapter 8, multi-currency fact tables must preserve both the original local transaction currency amount and the converted corporate reporting currency amount on every fact record to support both operational vendor management and corporate financial rollups simultaneously. Currency conversions must be linked to a conformed daily currency exchange rate dimension capturing spot rates. When goods are received and invoices are paid on later dates, fluctuations between the order spot rate and payment settlement spot rate produce realized foreign exchange (FX) variance (gain/loss), which must be tracked and reconciled with zero floating-point drift.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `ACCUMULATING_SNAPSHOT_FACT`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `dim_global_procurement_customer_core` | `DIMENSION` | `customer_sk` | 7 |
| `fact_global_procurement_orders` | `FACT` | `order_id` | 4 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Consolidated Corporate USD Reporting Spend | `scalar_eq` | `23700.0` | `23700.0` | `0.44ms` | ✅ PASS |
| Net Realized Foreign Exchange Variance Reconciled | `scalar_eq` | `400.0` | `400.0` | `0.4ms` | ✅ PASS |
| Spot Rate Triangulation Invariance Verification | `zero_drift` | `0.0` | `0.0` | `0.38ms` | ✅ PASS |
| Supplier Local vs Corporate Spend Breakdown | `scalar_eq` | `10800.0` | `10800.0` | `0.35ms` | ✅ PASS |

### Query Details
#### Query 1: Consolidated Corporate USD Reporting Spend
```sql
SELECT CAST(ROUND(SUM(reporting_usd_amount), 2) AS DOUBLE) FROM fact_procurement_orders;

```
#### Query 2: Net Realized Foreign Exchange Variance Reconciled
```sql
SELECT CAST(ROUND(SUM(realized_fx_variance_usd), 2) AS DOUBLE) FROM fact_procurement_orders;

```
#### Query 3: Spot Rate Triangulation Invariance Verification
```sql
SELECT CAST(ROUND(SUM(local_amount * order_spot_rate - reporting_usd_amount), 4) AS DOUBLE) FROM fact_procurement_orders;

```
#### Query 4: Supplier Local vs Corporate Spend Breakdown
```sql
SELECT CAST(ROUND(SUM(reporting_usd_amount), 2) AS DOUBLE) FROM fact_procurement_orders WHERE supplier_sk = 'SUP-EU-01';

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*