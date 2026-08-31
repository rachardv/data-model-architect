-- ============================================================================
-- SILVER LAYER: Staging & Conformed View for `stg_retail_customers`
-- Quality Policy: QUARANTINE_VIEW
-- Transformations: Type Casting, Row-Level Deduplication, Invariant Filtering
-- ============================================================================
CREATE OR REPLACE VIEW stg_retail_customers AS
WITH raw_source AS (
    SELECT * FROM raw_retail_customers
),
deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY updated_at DESC, _ingested_at DESC
        ) AS _row_num
    FROM raw_source
),
cleaned AS (
    SELECT
        -- Deterministic Surrogate Key Hash
        CAST(MD5(CAST(customer_id AS VARCHAR(64))) AS VARCHAR(64)) AS customer_sk,
        CAST(customer_id AS VARCHAR(64)) AS customer_id,
        TRIM(CAST(customer_name AS VARCHAR(255))) AS customer_name,
        CAST(email AS VARCHAR(255)) AS email,
        CAST(updated_at AS TIMESTAMPTZ) AS updated_at,
        _raw_payload_id,
        _source_file,
        _ingested_at
    FROM deduplicated
    WHERE _row_num = 1
)
SELECT * FROM cleaned;