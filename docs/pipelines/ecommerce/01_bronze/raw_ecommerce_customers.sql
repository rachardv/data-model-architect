-- ============================================================================
-- BRONZE LAYER: Raw Landing Ingestion Schema for `customers`
-- Ingestion Strategy: Append-Only Immutable Raw Event Ledger
-- ============================================================================
CREATE TABLE raw_ecommerce_customers (
    customer_id                  VARCHAR(64),
    customer_name                VARCHAR(255),
    email                        VARCHAR(255),
    updated_at                   TIMESTAMPTZ,
    -- Audit Metadata Tracking
    _raw_payload_id              VARCHAR(64) NOT NULL,
    _source_file                 VARCHAR(255) NOT NULL DEFAULT 'stream_ingest',
    _ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Sample Test Data Harness (Self-Contained Verification)
INSERT INTO raw_ecommerce_customers (customer_id, customer_name, email, updated_at, _raw_payload_id, _source_file, _ingested_at)
VALUES 
    ('CUST-1001', 'Alice Smith', 'alice@example.com', '2026-01-15 10:00:00 UTC', 'PAYLOAD-001', 'seed_data.csv', CURRENT_TIMESTAMP),
    ('CUST-1001', 'Alice Smith-Jones', 'alice.sj@example.com', '2026-06-20 14:30:00 UTC', 'PAYLOAD-002', 'seed_data.csv', CURRENT_TIMESTAMP),
    ('CUST-1002', 'Bob Johnson', 'bob@example.com', '2026-02-01 09:15:00 UTC', 'PAYLOAD-003', 'seed_data.csv', CURRENT_TIMESTAMP);