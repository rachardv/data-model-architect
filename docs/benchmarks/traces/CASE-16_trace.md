# Decision Trace Report: CASE-16 — Enterprise Multi-Source CRM and Billing Data Vault 2.0 Raw Ingestion Layer

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `3221.34ms`
> **Timestamp (UTC):** `2026-09-23T21:19:52.011470+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `enterprise_integration`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Dan Linstedt & Michael Olschimke (2015), "Building a Scalable Data Warehouse with Data Vault 2.0: Analyzing and Managing Big Data", Morgan Kaufmann / Elsevier, Chapters 3, 4 & 7 ("The Data Vault Architecture, Modeling Hubs, Links, and Satellites").
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
An enterprise B2B conglomerate acquires customer profile and financial relationship data from two independent operational source systems: a global Salesforce CRM instance (SRC_SALESFORCE_CRM) and a Stripe/SAP Billing ledger (SRC_STRIPE_BILLING). Both systems generate customer natural business keys independently, but customers also possess linked billing accounts. Business analysts and compliance auditors require a single auditable raw integration layer that preserves 100% of historical deltas without destructive overwrites, avoids ETL orchestration deadlocks between CRM and Billing batch windows, and supports reconstructed Point-in-Time (PIT) Customer 360 views. Per Dan Linstedt & Michael Olschimke (2015), we require a Data Vault 2.0 Raw Vault containing Hubs (hub_customer, hub_account), an association Link (link_customer_account), and isolated source-specific Satellites (sat_crm_customer, sat_billing_customer) keyed on deterministic SHA-256 hash keys, append-only load timestamps, and hash diff attributes.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `DATA_VAULT_2_RAW`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `hub_customer` | `HUB` | `customer_hk` | 4 |
| `hub_account` | `HUB` | `account_hk` | 4 |
| `link_customer_account` | `LINK` | `link_cust_account_hk` | 5 |
| `sat_crm_customer` | `SATELLITE` | `customer_hk, load_dts` | 7 |
| `sat_billing_customer` | `SATELLITE` | `customer_hk, load_dts` | 6 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Reconstructed Customer 360 Current Profile Credit Limit for Enterprise Tier | `scalar_eq` | `250000.0` | `250000.0` | `2.56ms` | ✅ PASS |
| Point-in-Time Historical PIT Credit Limit Before Increase | `scalar_eq` | `50000.0` | `50000.0` | `1.13ms` | ✅ PASS |
| Zero Orphan Foreign Hash Keys in Customer Account Link | `scalar_eq` | `0` | `0` | `0.7ms` | ✅ PASS |
| Multi-Source Satellite System Isolation Distinct Sources | `scalar_eq` | `2` | `2` | `0.55ms` | ✅ PASS |

### Query Details
#### Query 1: Reconstructed Customer 360 Current Profile Credit Limit for Enterprise Tier
```sql
WITH latest_crm AS (
    SELECT customer_hk, customer_name, crm_tier,
           ROW_NUMBER() OVER (PARTITION BY customer_hk ORDER BY load_dts DESC) as rn
    FROM sat_crm_customer
), latest_billing AS (
    SELECT customer_hk, credit_limit_usd, billing_status,
           ROW_NUMBER() OVER (PARTITION BY customer_hk ORDER BY load_dts DESC) as rn
    FROM sat_billing_customer
) SELECT CAST(ROUND(SUM(b.credit_limit_usd), 2) AS DOUBLE) FROM hub_customer h JOIN latest_crm c ON h.customer_hk = c.customer_hk AND c.rn = 1 JOIN latest_billing b ON h.customer_hk = b.customer_hk AND b.rn = 1 WHERE c.crm_tier = 'ENTERPRISE';

```
#### Query 2: Point-in-Time Historical PIT Credit Limit Before Increase
```sql
WITH pit_billing AS (
    SELECT customer_hk, credit_limit_usd,
           ROW_NUMBER() OVER (PARTITION BY customer_hk ORDER BY load_dts DESC) as rn
    FROM sat_billing_customer
    WHERE load_dts <= '2026-01-10 00:00:00+00'
) SELECT CAST(ROUND(b.credit_limit_usd, 2) AS DOUBLE) FROM hub_customer h JOIN pit_billing b ON h.customer_hk = b.customer_hk AND b.rn = 1 WHERE h.customer_id = 'CUST-1002';

```
#### Query 3: Zero Orphan Foreign Hash Keys in Customer Account Link
```sql
SELECT COUNT(*) FROM link_customer_account l LEFT JOIN hub_customer c ON l.customer_hk = c.customer_hk LEFT JOIN hub_account a ON l.account_hk = a.account_hk WHERE c.customer_hk IS NULL OR a.account_hk IS NULL;

```
#### Query 4: Multi-Source Satellite System Isolation Distinct Sources
```sql
SELECT COUNT(DISTINCT rec_src) FROM (
    SELECT rec_src FROM sat_crm_customer
    UNION ALL
    SELECT rec_src FROM sat_billing_customer
);

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*