-- ============================================================================
-- BRONZE LAYER: Raw Landing Ingestion Schema for `orders`
-- Ingestion Strategy: Append-Only Immutable Raw Event Ledger
-- ============================================================================
CREATE TABLE raw_retail_orders (
    order_id                     BIGINT,
    customer_id                  VARCHAR(64),
    total_amount                 DECIMAL(14,2),
    order_status                 VARCHAR(32),
    order_timestamp              TIMESTAMPTZ,
    -- Audit Metadata Tracking
    _raw_payload_id              VARCHAR(64) NOT NULL,
    _source_file                 VARCHAR(255) NOT NULL DEFAULT 'stream_ingest',
    _ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Sample Test Data Harness (Self-Contained Verification)
INSERT INTO raw_retail_orders (order_id, customer_id, total_amount, order_status, order_timestamp, _raw_payload_id, _source_file, _ingested_at)
VALUES 
    (5001, 'CUST-1001', 149.50, 'DELIVERED', '2026-02-10 11:20:00 UTC', 'PAYLOAD-004', 'seed_data.csv', CURRENT_TIMESTAMP),
    (5002, 'CUST-1002', 89.00, 'SHIPPED', '2026-02-11 15:45:00 UTC', 'PAYLOAD-005', 'seed_data.csv', CURRENT_TIMESTAMP),
    (5003, 'CUST-1001', -25.00, 'REJECTED_TEST', '2026-02-12 18:00:00 UTC', 'PAYLOAD-006', 'seed_data.csv', CURRENT_TIMESTAMP);