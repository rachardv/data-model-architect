-- ============================================================================
-- SILVER LAYER: Quarantine Exception View for `quarantine_retail_orders`
-- Captures all rejected records failing Data Contract invariants
-- ============================================================================
CREATE OR REPLACE VIEW quarantine_retail_orders AS
WITH raw_source AS (
    SELECT * FROM raw_retail_orders
),
deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY order_status DESC, _ingested_at DESC
        ) AS _row_num
    FROM raw_source
)
SELECT
    *,
    CASE
        WHEN NOT (total_amount >= 0.00) THEN 'FAILED_INVARIANT: total_amount >= 0.00'
        ELSE 'UNKNOWN_REJECTION'
    END AS quarantine_reason,
    CURRENT_TIMESTAMP AS quarantined_at
FROM deduplicated
WHERE _row_num = 1
  AND (NOT (total_amount >= 0.00));