-- Staging Orders: parse timestamps and standardize status
SELECT
    order_id,
    customer_id,
    LOWER(TRIM(order_status)) AS order_status,
    CAST(order_purchase_timestamp AS TIMESTAMP) AS purchase_timestamp,
    CAST(order_approved_at AS TIMESTAMP) AS approved_at,
    CAST(order_delivered_carrier_date AS TIMESTAMP) AS delivered_carrier_at,
    CAST(order_delivered_customer_date AS TIMESTAMP) AS delivered_customer_at,
    CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimated_delivery_at
FROM raw_olist_orders;
