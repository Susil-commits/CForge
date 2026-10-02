-- Staging Order Items: parse pricing and shipping deadlines
SELECT
    order_id,
    CAST(order_item_id AS INTEGER) AS order_item_id,
    product_id,
    seller_id,
    CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_timestamp,
    CAST(price AS DOUBLE) AS item_price,
    CAST(freight_value AS DOUBLE) AS freight_value
FROM raw_olist_order_items;
