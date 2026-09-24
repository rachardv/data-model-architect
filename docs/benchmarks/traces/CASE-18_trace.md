# Decision Trace Report: CASE-18 — Real-Time Columnar Streaming Ad Telemetry and Clickstream Mart

> **Verdict:** 🟢 PASS | **Type:** `✅ VALID DOMAIN MODEL` | **Runtime:** `3200.25ms`
> **Timestamp (UTC):** `2026-09-24T00:46:34.696999+00:00`

## 1. Case Metadata, Provenance & Intent
- **Domain:** `telemetry`
- **Hazard Category:** `CLEAN_BASELINE`
- **Provenance / Citation:** *Alexey Milovidov et al. (2024), "ClickHouse: Ultra-Fast Analytical DBMS Architecture", ClickHouse Documentation & VLDB. Also Apache Pinot Real-Time Distributed Columnar OLAP Engine (VLDB 2021).
*
- **Expected Status:** `CERTIFIED_PRODUCTION_READY`
- **Observed Final Status:** `CERTIFIED_PRODUCTION_READY`

### Business Prompt Narrative
```text
An ad-tech programmatic bidding platform processes over 100,000 real-time ad impression and click events per second. Marketing analytics teams and automated bidder engines require real-time campaign performance dashboards reporting Return on Ad Spend (ROAS), conversion rates, and unique visitor reach over rolling 5-minute sliding windows with sub-second p99 latency. Traditional normalized star schemas fail under this workload due to foreign key join overhead and write contention on dimension tables. Per Alexey Milovidov et al. (2024) and Apache Pinot architecture standards, we require a Real-Time Columnar Streaming OLAP table (stream_ad_clicks) where all dimensional attributes (campaign, ad placement, visitor, device category, geo country) are denormalized directly into the high-velocity streaming event record at ingestion time. Analytical queries must compute sub-second aggregations, utilize HyperLogLog approximate distinct counting (approx_count_distinct) for visitor reach, and execute with zero joins.

```

## 2. Intake & Architectural Decisions
- **Completeness Score:** `0.0%`
- **Selected Paradigm:** `REALTIME_STREAMING_OLAP`
- **Resolution Applied:** `None`

## 3. Synthesized Schema Tables
| Table Name | Type | Primary Key | Column Count |
| :--- | :--- | :--- | :--- |
| `stream_telemetry_clicks` | `STREAMING_FACT` | `event_id` | 10 |

## 4. Physical Verification Queries & Assertions
| Query Name | Assertion | Expected | Actual | Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Real-Time Campaign Return on Ad Spend ROAS | `scalar_eq` | `3.75` | `3.75` | `0.58ms` | ✅ PASS |
| HyperLogLog Approximate Unique Visitor Reach | `scalar_eq` | `3` | `3` | `0.38ms` | ✅ PASS |
| Sliding Window Conversion Rate | `scalar_eq` | `0.33` | `0.33` | `0.47ms` | ✅ PASS |
| Total Real-Time Streaming Events Ingested | `scalar_eq` | `5` | `5` | `0.23ms` | ✅ PASS |

### Query Details
#### Query 1: Real-Time Campaign Return on Ad Spend ROAS
```sql
SELECT CAST(ROUND(SUM(revenue_usd) / SUM(bid_cost_usd), 2) AS DOUBLE) FROM stream_ad_clicks WHERE campaign_id = 'CMP-901';

```
#### Query 2: HyperLogLog Approximate Unique Visitor Reach
```sql
SELECT CAST(approx_count_distinct(visitor_id) AS BIGINT) FROM stream_ad_clicks WHERE campaign_id = 'CMP-901';

```
#### Query 3: Sliding Window Conversion Rate
```sql
SELECT CAST(ROUND(COUNT(*) FILTER (WHERE is_converted = true) * 1.0 / COUNT(*), 2) AS DOUBLE) FROM stream_ad_clicks WHERE campaign_id = 'CMP-901';

```
#### Query 4: Total Real-Time Streaming Events Ingested
```sql
SELECT COUNT(*) FROM stream_ad_clicks;

```

---
*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*