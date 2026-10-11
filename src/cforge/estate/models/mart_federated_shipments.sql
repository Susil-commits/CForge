-- Federated Shipments Mart: Cross-catalog reconciliation between marketplace and external fulfillment
WITH fed_orders AS (
    SELECT
        nw.order_id AS external_order_id,
        nw.customer_id AS external_customer_id,
        nw.ship_via AS carrier_code,
        nw.order_date AS order_placed_date,
        ol.order_status AS marketplace_status,
        ROW_NUMBER() OVER (PARTITION BY nw.customer_id ORDER BY nw.order_date) AS order_sequence_rank
    FROM raw_nw_orders nw
    JOIN stg_orders ol ON nw.order_id = ol.order_id
)
SELECT
    f.external_order_id,
    f.external_customer_id,
    f.marketplace_status,
    f.order_sequence_rank,
    -- Correlated arithmetic subquery: misses stg_order_items.order_id dependency in AST lineage
    100.0 * (SELECT COUNT(*) FROM stg_order_items i WHERE i.order_id = f.external_order_id) / NULLIF(f.carrier_code, 0) AS carrier_item_ratio
FROM fed_orders f;
