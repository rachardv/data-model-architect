# Decision Trace Report: CASE-09 — Bitemporal Insurance Policy & SCD6 Splicing Lifecycle

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `198.71ms`
> **Timestamp (UTC):** `2026-09-23T20:43:59.288187+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `insurance_policy`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Ralph Kimball & Margy Ross (2013), "The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling" (3rd Edition), Chapter 5 ("Slowly Changing Dimension Techniques: Type 6 Hybrid Dimensions & Late-Arriving Data"), pp. 153-188, and Martin Fowler (2005), "Bitemporal History".
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
We operate an enterprise commercial property and casualty insurance carrier managing complex policy endorsements and claims lifecycles. Underwriting endorsements frequently occur retroactively, requiring historical policy timelines to be spliced into strict closed-open intervals without overlapping validity dates. Claims often arrive out-of-order weeks after an incident occurs, referencing policies that have not yet completed ETL ingestion; these must resolve to inferred ghost dimension records with sentinel surrogate keys to prevent catastrophic claim drop-outs. To support executive management and actuarial audits simultaneously, the policy dimension must implement Kimball SCD Type 6 hybrid attributes: preserving historical point-in-time risk tiers and sales territories (as-was) while maintaining current overwritten attributes (as-is) across all version slices.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `KIMBALL_STAR_SCD6`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `dim_insurance_policy_scd6` | `DIMENSION` | `policy_sk` | 12 |
| `fact_insurance_policy_claims` | `FACT` | `claim_id` | 5 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Zero Interval Overlap in Policy Dimension | `scalar_eq` | `0` | `0` | `0.82ms` | ✅ PASS |
| Late Arriving Ghost Policy Exists | `scalar_gt` | `0` | `1` | `0.31ms` | ✅ PASS |
| Zero Dropped Claims With Ghost Key Joins | `scalar_eq` | `4` | `4` | `0.61ms` | ✅ PASS |
| Historical Point In Time Risk Tier Aggregation | `scalar_gt` | `0` | `1` | `1.32ms` | ✅ PASS |
| Current Perspective Risk Tier Aggregation | `scalar_gt` | `0` | `1` | `0.98ms` | ✅ PASS |

### Query Details
#### Query 1: Zero Interval Overlap in Policy Dimension
```sql
SELECT COUNT(*) FROM (
  SELECT a.policy_id, a.policy_sk AS sk_a, b.policy_sk AS sk_b
  FROM dim_insurance_policy_scd6 a
  JOIN dim_insurance_policy_scd6 b ON a.policy_id = b.policy_id AND a.policy_sk <> b.policy_sk
  WHERE a.scd_valid_from < b.scd_valid_to AND b.scd_valid_from < a.scd_valid_to
);

```
#### Query 2: Late Arriving Ghost Policy Exists
```sql
SELECT COUNT(*) FROM dim_insurance_policy_scd6 WHERE is_inferred = true;
```
#### Query 3: Zero Dropped Claims With Ghost Key Joins
```sql
SELECT COUNT(*) FROM fact_insurance_policy_claims f JOIN dim_insurance_policy_scd6 d ON f.policy_sk = d.policy_sk WHERE f.claim_id >= 80001;
```
#### Query 4: Historical Point In Time Risk Tier Aggregation
```sql
WITH hist_summary AS (
  SELECT d.historical_risk_tier, SUM(f.claim_amount) AS total_claims
  FROM fact_insurance_policy_claims f
  JOIN dim_insurance_policy_scd6 d ON f.policy_sk = d.policy_sk
  WHERE f.claim_id >= 80001 AND d.historical_risk_tier = 'LOW'
  GROUP BY d.historical_risk_tier
) SELECT COUNT(*) FROM hist_summary WHERE total_claims = 12500.00;

```
#### Query 5: Current Perspective Risk Tier Aggregation
```sql
WITH curr_summary AS (
  SELECT d.current_risk_tier, SUM(f.claim_amount) AS total_claims
  FROM fact_insurance_policy_claims f
  JOIN dim_insurance_policy_scd6 d ON f.policy_sk = d.policy_sk
  WHERE f.claim_id >= 80001 AND d.current_risk_tier = 'HIGH'
  GROUP BY d.current_risk_tier
) SELECT COUNT(*) FROM curr_summary WHERE total_claims = 65500.00;

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*