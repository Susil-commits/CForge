-- Mart Geo Performance: Geographic regional delivery SLA performance and freight economics
SELECT
    customer_state AS state_code,
    customer_city,
    COUNT(order_id) AS total_orders,
    ROUND(SUM(grand_total_brl), 2) AS regional_gmv_brl,
    ROUND(AVG(freight_total_brl), 2) AS avg_freight_cost_brl,
    ROUND(AVG(customer_review_score), 2) AS avg_regional_satisfaction,
    SUM(CASE WHEN is_delayed_delivery THEN 1 ELSE 0 END) AS delayed_orders_count,
    ROUND(100.0 * SUM(CASE WHEN is_delayed_delivery THEN 1 ELSE 0 END) / NULLIF(COUNT(order_id), 0), 2) AS delay_rate_percentage
FROM fct_orders
WHERE customer_state IS NOT NULL
GROUP BY customer_state, customer_city;
