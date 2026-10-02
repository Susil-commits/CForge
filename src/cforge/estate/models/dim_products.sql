-- Dimension Products: Master product catalog with categorization and weight tiers
SELECT
    product_id,
    category_english AS product_category,
    category_portuguese AS raw_category_name,
    weight_g AS product_weight_grams,
    volume_cm3 AS product_volume_cm3,
    photos_count AS catalog_photo_count,
    CASE 
        WHEN weight_g IS NULL THEN 'unknown'
        WHEN weight_g < 500 THEN 'lightweight'
        WHEN weight_g < 2000 THEN 'medium_weight'
        ELSE 'heavyweight'
    END AS weight_class
FROM stg_products;
