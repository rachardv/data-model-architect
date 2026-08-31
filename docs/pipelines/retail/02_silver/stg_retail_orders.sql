-- ============================================================================
-- SILVER LAYER: Staging & Conformed View for `stg_retail_orders`
-- Quality Policy: QUARANTINE_VIEW
-- Transformations: Type Casting, Row-Level Deduplication, Invariant Filtering
-- ============================================================================
CREATE OR REPLACE VIEW stg_retail_orders AS
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
),
cleaned AS (
    SELECT
        -- Deterministic Surrogate Key Hash
        CAST(MD5(CAST(order_id AS VARCHAR(64))) AS VARCHAR(64)) AS order_sk,
        CAST(order_id AS BIGINT) AS order_id,
        CAST(customer_id AS VARCHAR(64)) AS customer_id,
        CAST(total_amount AS DECIMAL(14,2)) AS total_amount,
        UPPER(TRIM(CAST(order_status AS VARCHAR(32)))) AS order_status,
        CAST(order_timestamp AS TIMESTAMPTZ) AS order_timestamp,
        _raw_payload_id,
        _source_file,
        _ingested_at
    FROM deduplicated
    WHERE _row_num = 1
      AND total_amount >= 0.00
)
SELECT * FROM cleaned;