-- Staging Products: translate category names and compute cubic volume
SELECT
    p.product_id,
    p.product_category_name AS category_portuguese,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unspecified') AS category_english,
    CAST(p.product_name_lenght AS INTEGER) AS name_char_length,
    CAST(p.product_description_lenght AS INTEGER) AS description_char_length,
    CAST(p.product_photos_qty AS INTEGER) AS photos_count,
    CAST(p.product_weight_g AS DOUBLE) AS weight_g,
    CAST(p.product_length_cm AS DOUBLE) AS length_cm,
    CAST(p.product_height_cm AS DOUBLE) AS height_cm,
    CAST(p.product_width_cm AS DOUBLE) AS width_cm,
    CAST(COALESCE(p.product_length_cm, 0) * COALESCE(p.product_height_cm, 0) * COALESCE(p.product_width_cm, 0) AS DOUBLE) AS volume_cm3
FROM raw_olist_products p
LEFT JOIN raw_olist_category_translation t 
    ON p.product_category_name = t.product_category_name;
