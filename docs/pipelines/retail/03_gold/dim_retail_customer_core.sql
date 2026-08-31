-- ============================================================================
-- GOLD LAYER: SCD Type 2 Merge Pipeline for `dim_retail_customer_core`
-- Strategy: ANSI_MERGE
-- ============================================================================
-- Step 1: Atomic SCD2 Merge & Interval Closure Script
MERGE INTO dim_retail_customer_core AS target
USING stg_retail_customers AS source
ON (target.customer_id = source.customer_id AND target.scd_valid_to = '9999-12-31 23:59:59 UTC')

-- Scenario A: Existing Record Changed -> Close Validity Interval
WHEN MATCHED AND (target.customer_name != source.customer_name OR target.customer_id != source.customer_id) THEN
    UPDATE SET
        scd_valid_to = source.updated_at

-- Scenario B: New Entity Record -> Insert New Active Version
WHEN NOT MATCHED THEN
    INSERT (
        customer_sk, customer_id, customer_name, scd_valid_from, scd_valid_to
    )
    VALUES (
        source.customer_sk, source.customer_id, source.customer_name, source.updated_at, '9999-12-31 23:59:59 UTC'
    );

-- Companion Gold View: Current Active State Only
CREATE OR REPLACE VIEW v_current_dim_retail_customer_core AS
SELECT * FROM dim_retail_customer_core WHERE scd_valid_to = '9999-12-31 23:59:59 UTC';