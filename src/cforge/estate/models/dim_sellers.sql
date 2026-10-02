-- Dimension Sellers: Seller metrics, fulfillment volume, and lifetime merchandise value
WITH seller_sales AS (
    SELECT
        s.seller_id,
        MIN(s.seller_city) AS seller_city,
        MIN(s.seller_state) AS seller_state,
        MIN(s.zip_code_prefix) AS seller_zip,
        COUNT(oi.order_id) AS total_items_sold,
        COALESCE(SUM(oi.item_price), 0.0) AS total_merchandise_revenue,
        COALESCE(AVG(oi.item_price), 0.0) AS avg_item_sale_price
    FROM stg_sellers s
    LEFT JOIN stg_order_items oi ON s.seller_id = oi.seller_id
    GROUP BY s.seller_id
)
SELECT
    seller_id,
    seller_city,
    seller_state,
    seller_zip,
    total_items_sold,
    ROUND(total_merchandise_revenue, 2) AS total_revenue_brl,
    ROUND(avg_item_sale_price, 2) AS average_ticket_brl,
    CASE 
        WHEN total_merchandise_revenue > 10000 THEN 'tier_1_top_seller'
        WHEN total_merchandise_revenue > 2000 THEN 'tier_2_growth_seller'
        ELSE 'tier_3_standard_seller'
    END AS seller_tier
FROM seller_sales;
