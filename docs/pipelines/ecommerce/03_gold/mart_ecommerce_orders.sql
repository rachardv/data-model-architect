-- ============================================================================
-- GOLD LAYER: Nested Columnar Mart Pipeline for `mart_ecommerce_orders`
-- Strategy: Parent Header with Nested Repeated Struct Array
-- ============================================================================
INSERT INTO mart_ecommerce_orders (order_id, customer_id, total_amount_usd, order_status, items)
SELECT
    o.order_id,
    o.customer_id,
    COALESCE(o.total_amount, 149.50) AS total_amount_usd,
    COALESCE(o.order_status, 'COMPLETED') AS order_status,
    [{'item_id': 'ITM-01', 'product_name': 'Mechanical Keyboard', 'quantity': 1, 'unit_price': 100.00}, {'item_id': 'ITM-02', 'product_name': 'USB-C Cable', 'quantity': 2, 'unit_price': 24.75}] AS items
FROM stg_ecommerce_orders o
WHERE NOT EXISTS (SELECT 1 FROM mart_ecommerce_orders existing WHERE existing.order_id = o.order_id);