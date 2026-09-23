# Decision Trace Report: CASE-17 — Anti-Money Laundering Financial Transfer Network and Circular Mule Ring Detection

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `3274.19ms`
> **Timestamp (UTC):** `2026-09-23T21:19:48.268122+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `aml_fraud`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Ian Robinson, Jim Webber & Emil Eifrem (2015), "Graph Databases: New Opportunities for Connected Data" (2nd Edition), O'Reilly Media, Chapters 1, 3 & 6 ("Connected Data in Practice, Path Traversals, and Cycle Detection").
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
An AML financial crime investigation unit at a major tier-1 bank monitors wire and instant electronic funds transfers to detect criminal money laundering syndicates and structuring networks. Criminal organizations routinely execute circular money mule rings: illicit funds originate at a source shell account, bounce through multiple intermediary accounts to obfuscate the source of funds, and circulate back to the originating entity or an affiliated beneficiary (e.g. Account 201 -> Account 202 -> Account 203 -> Account 201). Traditional dimensional star schemas fail to detect these closed directed cycles without brittle, pre-specified join chains. Per Robinson, Webber & Eifrem (2015), we require a Graph OLAP network topology comprising an account vertex table (graph_account_nodes) and a directed funds transfer edge table (graph_transfer_edges). Analytical queries must execute recursive path traversal in DuckDB to identify closed cycles (Cycle Depth >= 3), calculate nodal out-degree fan-out ratios, and isolate criminal rings.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `GRAPH_PROPERTY_TOPOLOGY`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `graph_aml_fraud_account_nodes` | `VERTEX` | `account_id` | 4 |
| `graph_aml_fraud_transfer_edges` | `EDGE` | `edge_id` | 5 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Recursive Closed Cycle Detection for Depth 3 Mule Ring | `scalar_eq` | `3` | `3` | `2.83ms` | ✅ PASS |
| Total Laundered Volume in Circular Ring | `scalar_eq` | `29300.0` | `29300.0` | `0.48ms` | ✅ PASS |
| High-Fan-Out Structuring Hub Out-Degree | `scalar_eq` | `3` | `3` | `0.71ms` | ✅ PASS |
| Linear Legitimate Chain Cycle Immunity | `scalar_eq` | `0` | `0` | `1.42ms` | ✅ PASS |

### Query Details
#### Query 1: Recursive Closed Cycle Detection for Depth 3 Mule Ring
```sql
WITH RECURSIVE transfer_paths AS (
    SELECT 
        source_account_id AS root_node,
        target_account_id,
        amount_usd,
        1 AS hop_depth,
        [source_account_id, target_account_id] AS path,
        (source_account_id = target_account_id) AS is_cycle
    FROM graph_transfer_edges
    UNION ALL
    SELECT 
        p.root_node,
        e.target_account_id,
        e.amount_usd,
        p.hop_depth + 1,
        list_append(p.path, e.target_account_id),
        (e.target_account_id = p.root_node) AS is_cycle
    FROM transfer_paths p
    JOIN graph_transfer_edges e ON p.target_account_id = e.source_account_id
    WHERE p.hop_depth < 4
      AND NOT (list_contains(p.path[2:], e.target_account_id))
) SELECT COUNT(DISTINCT root_node) FROM transfer_paths WHERE is_cycle = true AND hop_depth = 3;

```
#### Query 2: Total Laundered Volume in Circular Ring
```sql
SELECT CAST(ROUND(SUM(amount_usd), 2) AS DOUBLE) FROM graph_transfer_edges WHERE source_account_id IN ('ACCT-201', 'ACCT-202', 'ACCT-203')
  AND target_account_id IN ('ACCT-201', 'ACCT-202', 'ACCT-203');

```
#### Query 3: High-Fan-Out Structuring Hub Out-Degree
```sql
SELECT COUNT(DISTINCT target_account_id) FROM graph_transfer_edges WHERE source_account_id = 'ACCT-301';

```
#### Query 4: Linear Legitimate Chain Cycle Immunity
```sql
WITH RECURSIVE linear_paths AS (
    SELECT 
        source_account_id AS root_node,
        target_account_id,
        1 AS hop_depth,
        [source_account_id, target_account_id] AS path,
        (source_account_id = target_account_id) AS is_cycle
    FROM graph_transfer_edges
    WHERE source_account_id = 'ACCT-101'
    UNION ALL
    SELECT 
        p.root_node,
        e.target_account_id,
        p.hop_depth + 1,
        list_append(p.path, e.target_account_id),
        (e.target_account_id = p.root_node) AS is_cycle
    FROM linear_paths p
    JOIN graph_transfer_edges e ON p.target_account_id = e.source_account_id
    WHERE p.hop_depth < 4
      AND NOT (list_contains(p.path[2:], e.target_account_id))
) SELECT COUNT(*) FROM linear_paths WHERE is_cycle = true;

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*