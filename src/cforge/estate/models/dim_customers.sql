-- Dimension Customers: Customer entity with geographic traits and aggregated order activity
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        MIN(c.customer_city) AS primary_city,
        MIN(c.customer_state) AS primary_state,
        MIN(c.zip_code_prefix) AS primary_zip,
        COUNT(DISTINCT o.order_id) AS total_orders_placed,
        MIN(o.purchase_timestamp) AS first_order_date,
        MAX(o.purchase_timestamp) AS latest_order_date
    FROM stg_customers c
    LEFT JOIN stg_orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT
    customer_unique_id,
    primary_city,
    primary_state,
    primary_zip,
    total_orders_placed,
    first_order_date,
    latest_order_date,
    CASE 
        WHEN total_orders_placed > 1 THEN 'repeat_buyer'
        ELSE 'single_buyer'
    END AS buyer_type
FROM customer_orders;
