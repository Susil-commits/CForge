-- Staging Payments: standardize payment sequences and amounts
SELECT
    order_id,
    CAST(payment_sequential AS INTEGER) AS payment_sequential,
    LOWER(TRIM(payment_type)) AS payment_type,
    CAST(payment_installments AS INTEGER) AS payment_installments,
    CAST(payment_value AS DOUBLE) AS payment_amount
FROM raw_olist_order_payments;
