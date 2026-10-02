-- Customer Lifetime Value Mart: RFM analysis, total revenue contribution, and lifetime segmentation
WITH customer_orders AS (
    SELECT
        customer_unique_id,
        primary_city,
        primary_state,
        primary_zip,
        total_orders_placed,
        first_order_date,
        latest_order_date
    FROM dim_customers
),
order_spend AS (
    SELECT
        customer_unique_id,
        COALESCE(SUM(grand_total_brl), 0.0) AS lifetime_spend_brl,
        COALESCE(AVG(grand_total_brl), 0.0) AS average_order_value_brl,
        COALESCE(AVG(customer_review_score), 5.0) AS avg_customer_rating
    FROM fct_orders
    WHERE customer_unique_id IS NOT NULL
    GROUP BY customer_unique_id
)
SELECT
    c.customer_unique_id,
    c.primary_city,
    c.primary_state,
    c.primary_zip,
    c.total_orders_placed,
    ROUND(COALESCE(s.lifetime_spend_brl, 0.0), 2) AS total_lifetime_spend_brl,
    ROUND(COALESCE(s.average_order_value_brl, 0.0), 2) AS avg_order_ticket_brl,
    ROUND(s.avg_customer_rating, 2) AS satisfaction_score,
    c.first_order_date,
    c.latest_order_date,
    CASE 
        WHEN COALESCE(s.lifetime_spend_brl, 0.0) >= 500.0 THEN 'High Value VIP'
        WHEN COALESCE(s.lifetime_spend_brl, 0.0) >= 150.0 THEN 'Mid Tier Core'
        ELSE 'Low Tier Standard'
    END AS ltv_segment
FROM customer_orders c
LEFT JOIN order_spend s ON c.customer_unique_id = s.customer_unique_id;
