-- ============================================================================
-- GOLD LAYER: Incremental Fact Pipeline for `fact_ecommerce_orders`
-- Strategy: Star Schema Incremental Load with Surrogate Key Resolution
-- ============================================================================
INSERT INTO fact_ecommerce_orders (
    order_id, customer_sk, total_amount_usd, estimated_delivery_days
)
SELECT
    o.order_id,
    COALESCE(c.customer_sk, 'UNKNOWN_SK') AS customer_sk,
    o.total_amount AS total_amount_usd,
    CAST(3 AS INT) AS estimated_delivery_days -- [AI-GENERATED FALLBACK]
FROM stg_ecommerce_orders o
LEFT JOIN v_current_dim_ecommerce_customer_core c
  ON o.customer_id = c.customer_id
WHERE NOT EXISTS (
    SELECT 1 FROM fact_ecommerce_orders existing WHERE existing.order_id = o.order_id
);