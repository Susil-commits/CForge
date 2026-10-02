-- Staging Customers: clean and standardize customer records
SELECT
    customer_id,
    customer_unique_id,
    CAST(customer_zip_code_prefix AS VARCHAR) AS zip_code_prefix,
    LOWER(TRIM(customer_city)) AS customer_city,
    UPPER(TRIM(customer_state)) AS customer_state
FROM raw_olist_customers;
