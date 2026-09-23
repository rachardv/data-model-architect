# Decision Trace Report: CASE-03 — Banking Multi-Owner Joint Account Co-Ownership

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `75.48ms`
> **Timestamp (UTC):** `2026-09-23T20:32:32.912577+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `banking`
- **Hazard Category:** `BRIDGE_CO_OWNERSHIP`
- **Provenance / Citation:** *Ralph Kimball & Margy Ross, The Data Warehouse Toolkit (3rd Edition), Chapter 11: "Financial Services", pp. 295-326 ("Joint Accounts and Co-Owners with Weighting Factors").
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
Consumer retail banking managing checking and savings accounts. Accounts can be jointly owned by multiple customers (primary and secondary account holders) using weighting factor splits. Transactions track deposits, withdrawals, and balances. Customer address and status changes are tracked historically using SCD Type 2.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `MULTIVALUED_BRIDGE_STAR`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `dim_banking_customer_core` | `DIMENSION` | `customer_sk` | 7 |
| `fact_banking_orders` | `FACT` | `order_id` | 4 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Active SCD2 Customers Check | `scalar_gt` | `0` | `2` | `0.28ms` | ✅ PASS |
| Transactions Fact Count | `scalar_gt` | `0` | `2` | `0.23ms` | ✅ PASS |
| Total Transaction Amount Sum | `scalar_gt` | `0.0` | `238.50` | `0.37ms` | ✅ PASS |

### Query Details
#### Query 1: Active SCD2 Customers Check
```sql
SELECT COUNT(*) FROM dim_banking_customer_core WHERE is_current = true;
```
#### Query 2: Transactions Fact Count
```sql
SELECT COUNT(*) FROM fact_banking_orders WHERE total_amount_usd >= 0;
```
#### Query 3: Total Transaction Amount Sum
```sql
SELECT SUM(total_amount_usd) FROM fact_banking_orders;
```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*