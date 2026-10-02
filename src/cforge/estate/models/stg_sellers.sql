-- Staging Sellers: standardize location and identifiers
SELECT
    seller_id,
    CAST(seller_zip_code_prefix AS VARCHAR) AS zip_code_prefix,
    LOWER(TRIM(seller_city)) AS seller_city,
    UPPER(TRIM(seller_state)) AS seller_state
FROM raw_olist_sellers;
