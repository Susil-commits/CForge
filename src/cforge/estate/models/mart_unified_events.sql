-- Unified Logistics and Fulfillment Events Mart
-- Complex Model featuring: Multi-stage CTEs, Window Functions (ROW_NUMBER, DENSE_RANK), and UNION ALL
WITH olist_deliveries AS (
    SELECT
        order_id AS event_id,
        customer_id AS party_id,
        'OLIST' AS platform_source,
        purchase_timestamp AS event_timestamp,
        delivered_customer_at AS fulfillment_timestamp,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY purchase_timestamp DESC) AS customer_seq_num
    FROM stg_orders
),
northwind_deliveries AS (
    SELECT
        order_id AS event_id,
        customer_id AS party_id,
        'NORTHWIND' AS platform_source,
        order_date AS event_timestamp,
        shipped_date AS fulfillment_timestamp,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS customer_seq_num
    FROM raw_nw_orders
),
combined_union AS (
    SELECT event_id, party_id, platform_source, event_timestamp, fulfillment_timestamp, customer_seq_num FROM olist_deliveries
    UNION ALL
    SELECT event_id, party_id, platform_source, event_timestamp, fulfillment_timestamp, customer_seq_num FROM northwind_deliveries
)
SELECT
    event_id,
    party_id,
    platform_source,
    event_timestamp,
    fulfillment_timestamp,
    customer_seq_num,
    DENSE_RANK() OVER (PARTITION BY platform_source ORDER BY event_timestamp DESC) AS recency_dense_rank
FROM combined_union;
