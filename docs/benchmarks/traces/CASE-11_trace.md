# Decision Trace Report: CASE-11 — SaaS Subscription Funnel Accumulating Snapshot & Milestone Lag

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `100.55ms`
> **Timestamp (UTC):** `2026-09-23T20:40:06.361599+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `saas_subscription`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Ralph Kimball & Margy Ross (2013), "The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling" (3rd Edition), Chapter 14 ("Accounting & Subscription Services: Accumulating Snapshot Fact Tables for Multi-Stage Lifecycle Funnels & Cohort Churn"), pp. 385-412.
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
We operate an enterprise B2B SaaS platform delivering cloud-based subscription software. Our go-to-market and customer success teams require visibility across the entire multi-stage customer lifecycle: from marketing lead generation, self-serve trial sign-up, paid contract activation, tier upgrades, annual renewal, through to eventual churn or cancellation. Because subscriptions evolve over time across well-defined operational milestones with variable duration between steps, standard transaction facts fail to answer funnel velocity questions efficiently. We require an accumulating snapshot fact table where each record represents a single subscription lifecycle journey. As a customer transitions across milestones, their accumulating snapshot record is progressively updated with milestone date keys and lag metrics (days from lead to trial, days from trial to activation, and total subscription lifetime days). BI dashboards must query milestone lag distributions, cohort conversion rates, active Monthly Recurring Revenue (MRR), and churn rates with zero Cartesian fan-out or temporal metric inflation.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `ACCUMULATING_SNAPSHOT_FACT`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `dim_saas_subscription_customer_core` | `DIMENSION` | `customer_sk` | 7 |
| `fact_saas_subscription_orders` | `FACT` | `order_id` | 4 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Active Enterprise MRR Sum | `scalar_eq` | `5000.0` | `5000.0` | `0.46ms` | ✅ PASS |
| Trial-to-Activation Conversion Rate | `scalar_eq` | `66.7` | `66.7` | `0.43ms` | ✅ PASS |
| Average Days from Trial to Activation for Activated Subscriptions | `scalar_eq` | `16.5` | `16.5` | `0.35ms` | ✅ PASS |
| Churn Cohort Count | `scalar_eq` | `2` | `2` | `0.31ms` | ✅ PASS |

### Query Details
#### Query 1: Active Enterprise MRR Sum
```sql
SELECT CAST(ROUND(SUM(mrr_amount_usd), 2) AS DOUBLE) FROM fact_subscription_funnel_accumulating WHERE is_active = true;

```
#### Query 2: Trial-to-Activation Conversion Rate
```sql
SELECT CAST(ROUND(CAST(COUNT(activation_date_key) AS DOUBLE) / COUNT(trial_date_key) * 100.0, 1) AS DOUBLE) FROM fact_subscription_funnel_accumulating;

```
#### Query 3: Average Days from Trial to Activation for Activated Subscriptions
```sql
SELECT CAST(ROUND(AVG(trial_to_activation_days), 1) AS DOUBLE) FROM fact_subscription_funnel_accumulating WHERE activation_date_key IS NOT NULL;

```
#### Query 4: Churn Cohort Count
```sql
SELECT COUNT(*) FROM fact_subscription_funnel_accumulating WHERE is_churned = true;

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*