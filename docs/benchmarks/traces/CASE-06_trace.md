# Decision Trace Report: CASE-06 — E-Commerce Orders with Nested Repeated Line Items

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `3076.74ms`
> **Timestamp (UTC):** `2026-09-23T19:03:54.209873+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `ecommerce`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Google Cloud BigQuery Architecture Guide (2024), "Data Modeling: Using Nested and Repeated Fields to Denormalize Parent-Child Relationships".
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
We operate a high-scale global e-commerce marketplace. Each customer order contains multiple order line items (nested repeated records). To eliminate join fan-out traps and optimize columnar scanning in modern data warehouses, orders and line items must be stored together in a nested columnar mart using STRUCT and ARRAY fields. Customer address and profile changes are tracked historically using SCD Type 2.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `NESTED_COLUMNAR_MART`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `dim_ecommerce_customer_core` | `DIMENSION` | `customer_sk` | 6 |
| `mart_ecommerce_orders` | `FACT` | `order_id` | 5 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Active SCD2 Customers Dimension Count | `scalar_gt` | `0` | `2` | `0.32ms` | ✅ PASS |
| Nested Mart Orders Count | `scalar_gt` | `0` | `2` | `0.27ms` | ✅ PASS |
| Unnested Line Items Projection Count | `row_count_gt` | `0` | `4` | `0.38ms` | ✅ PASS |
| Total Revenue from Unnested Line Items | `scalar_gt` | `0.0` | `299.00` | `0.49ms` | ✅ PASS |

### Query Details
#### Query 1: Active SCD2 Customers Dimension Count
```sql
SELECT COUNT(*) FROM dim_ecommerce_customer_core WHERE is_current = true;
```
#### Query 2: Nested Mart Orders Count
```sql
SELECT COUNT(*) FROM mart_ecommerce_orders WHERE total_amount_usd >= 0;
```
#### Query 3: Unnested Line Items Projection Count
```sql
SELECT order_id, unnest(items).product_name, unnest(items).quantity FROM mart_ecommerce_orders;
```
#### Query 4: Total Revenue from Unnested Line Items
```sql
WITH unnested_items AS (SELECT unnest(items) AS itm FROM mart_ecommerce_orders) SELECT SUM(itm.quantity * itm.unit_price) FROM unnested_items;
```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*