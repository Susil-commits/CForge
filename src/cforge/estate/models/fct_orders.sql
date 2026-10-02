-- Fact Orders: Grain is one order, enriched with customer details, items aggregate, and delivery SLA
WITH item_aggregates AS (
    SELECT
        order_id,
        COUNT(order_item_id) AS total_items,
        COUNT(DISTINCT product_id) AS distinct_products_count,
        COALESCE(SUM(item_price), 0.0) AS merchandise_subtotal,
        COALESCE(SUM(freight_value), 0.0) AS total_freight_amount
    FROM stg_order_items
    GROUP BY order_id
),
review_aggregates AS (
    SELECT
        order_id,
        AVG(review_score) AS average_review_score,
        COUNT(review_id) AS review_count
    FROM stg_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    c.customer_city,
    o.order_status,
    o.purchase_timestamp,
    o.approved_at,
    o.delivered_customer_at,
    o.estimated_delivery_at,
    COALESCE(ia.total_items, 0) AS total_order_items,
    COALESCE(ia.distinct_products_count, 0) AS distinct_products_count,
    ROUND(COALESCE(ia.merchandise_subtotal, 0.0), 2) AS merchandise_total_brl,
    ROUND(COALESCE(ia.total_freight_amount, 0.0), 2) AS freight_total_brl,
    ROUND(COALESCE(ia.merchandise_subtotal, 0.0) + COALESCE(ia.total_freight_amount, 0.0), 2) AS grand_total_brl,
    ROUND(ra.average_review_score, 1) AS customer_review_score,
    CASE 
        WHEN o.delivered_customer_at > o.estimated_delivery_at THEN TRUE
        ELSE FALSE
    END AS is_delayed_delivery
FROM stg_orders o
LEFT JOIN stg_customers c ON o.customer_id = c.customer_id
LEFT JOIN item_aggregates ia ON o.order_id = ia.order_id
LEFT JOIN review_aggregates ra ON o.order_id = ra.order_id;
