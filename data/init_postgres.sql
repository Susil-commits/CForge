-- ContextForge Real Estate PostgreSQL Initialization Script

-- Auto-generated for Docker Compose deployment

CREATE SCHEMA IF NOT EXISTS raw;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS public.customer_ltv (
    customer_unique_id VARCHAR,
    primary_city VARCHAR,
    primary_state VARCHAR,
    primary_zip VARCHAR,
    total_orders_placed BIGINT,
    total_lifetime_spend_brl NUMERIC(15, 4),
    avg_order_ticket_brl NUMERIC(15, 4),
    satisfaction_score NUMERIC(15, 4),
    first_order_date VARCHAR,
    latest_order_date VARCHAR,
    ltv_segment VARCHAR
);

CREATE TABLE IF NOT EXISTS public.dim_customers (
    customer_unique_id VARCHAR,
    primary_city VARCHAR,
    primary_state VARCHAR,
    primary_zip VARCHAR,
    total_orders_placed BIGINT,
    first_order_date VARCHAR,
    latest_order_date VARCHAR,
    buyer_type VARCHAR
);

CREATE TABLE IF NOT EXISTS public.dim_products (
    product_id VARCHAR,
    product_category VARCHAR,
    raw_category_name VARCHAR,
    product_weight_grams NUMERIC(15, 4),
    product_volume_cm3 NUMERIC(15, 4),
    catalog_photo_count BIGINT,
    weight_class VARCHAR
);

CREATE TABLE IF NOT EXISTS public.dim_sellers (
    seller_id VARCHAR,
    seller_city VARCHAR,
    seller_state VARCHAR,
    seller_zip VARCHAR,
    total_items_sold BIGINT,
    total_revenue_brl NUMERIC(15, 4),
    average_ticket_brl NUMERIC(15, 4),
    seller_tier VARCHAR
);

CREATE TABLE IF NOT EXISTS public.fct_order_payments (
    order_id VARCHAR,
    payment_sequential BIGINT,
    payment_type VARCHAR,
    payment_installments BIGINT,
    payment_amount NUMERIC(15, 4),
    is_credit_card_payment BOOLEAN,
    is_split_installment BOOLEAN
);

CREATE TABLE IF NOT EXISTS public.fct_orders (
    order_id VARCHAR,
    customer_id VARCHAR,
    customer_unique_id VARCHAR,
    customer_state VARCHAR,
    customer_city VARCHAR,
    order_status VARCHAR,
    purchase_timestamp VARCHAR,
    approved_at VARCHAR,
    delivered_customer_at VARCHAR,
    estimated_delivery_at VARCHAR,
    total_order_items BIGINT,
    distinct_products_count BIGINT,
    merchandise_total_brl NUMERIC(15, 4),
    freight_total_brl NUMERIC(15, 4),
    grand_total_brl NUMERIC(15, 4),
    customer_review_score NUMERIC(15, 4),
    is_delayed_delivery BOOLEAN
);

CREATE TABLE IF NOT EXISTS public.mart_geo_performance (
    state_code VARCHAR,
    customer_city VARCHAR,
    total_orders BIGINT,
    regional_gmv_brl NUMERIC(15, 4),
    avg_freight_cost_brl NUMERIC(15, 4),
    avg_regional_satisfaction NUMERIC(15, 4),
    delayed_orders_count BIGINT,
    delay_rate_percentage NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.raw_nw_categories (
    categoryID BIGINT,
    categoryName VARCHAR,
    description VARCHAR,
    picture VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_nw_customers (
    customerID VARCHAR,
    companyName VARCHAR,
    contactName VARCHAR,
    contactTitle VARCHAR,
    address VARCHAR,
    city VARCHAR,
    region VARCHAR,
    postalCode VARCHAR,
    country VARCHAR,
    phone VARCHAR,
    fax VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_nw_employees (
    employeeID BIGINT,
    lastName VARCHAR,
    firstName VARCHAR,
    title VARCHAR,
    titleOfCourtesy VARCHAR,
    birthDate VARCHAR,
    hireDate VARCHAR,
    address VARCHAR,
    city VARCHAR,
    region VARCHAR,
    postalCode VARCHAR,
    country VARCHAR,
    homePhone VARCHAR,
    extension BIGINT,
    photo VARCHAR,
    notes VARCHAR,
    reportsTo VARCHAR,
    photoPath VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_nw_order_details (
    orderID BIGINT,
    productID BIGINT,
    unitPrice NUMERIC(15, 4),
    quantity BIGINT,
    discount NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.raw_nw_orders (
    orderID BIGINT,
    customerID VARCHAR,
    employeeID BIGINT,
    orderDate VARCHAR,
    requiredDate VARCHAR,
    shippedDate VARCHAR,
    shipVia BIGINT,
    freight NUMERIC(15, 4),
    shipName VARCHAR,
    shipAddress VARCHAR,
    shipCity VARCHAR,
    shipRegion VARCHAR,
    shipPostalCode VARCHAR,
    shipCountry VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_nw_products (
    productID BIGINT,
    productName VARCHAR,
    supplierID BIGINT,
    categoryID BIGINT,
    quantityPerUnit VARCHAR,
    unitPrice NUMERIC(15, 4),
    unitsInStock BIGINT,
    unitsOnOrder BIGINT,
    reorderLevel BIGINT,
    discontinued BIGINT
);

CREATE TABLE IF NOT EXISTS public.raw_nw_shippers (
    shipperID BIGINT,
    companyName VARCHAR,
    phone VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_nw_suppliers (
    supplierID BIGINT,
    companyName VARCHAR,
    contactName VARCHAR,
    contactTitle VARCHAR,
    address VARCHAR,
    city VARCHAR,
    region VARCHAR,
    postalCode VARCHAR,
    country VARCHAR,
    phone VARCHAR,
    fax VARCHAR,
    homePage VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_olist_category_translation (
    product_category_name VARCHAR,
    product_category_name_english VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_olist_customers (
    customer_id VARCHAR,
    customer_unique_id VARCHAR,
    customer_zip_code_prefix BIGINT,
    customer_city VARCHAR,
    customer_state VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_olist_geolocation (
    geolocation_zip_code_prefix VARCHAR,
    geolocation_lat NUMERIC(15, 4),
    geolocation_lng NUMERIC(15, 4),
    geolocation_city VARCHAR,
    geolocation_state VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_olist_order_items (
    order_id VARCHAR,
    order_item_id BIGINT,
    product_id VARCHAR,
    seller_id VARCHAR,
    shipping_limit_date VARCHAR,
    price NUMERIC(15, 4),
    freight_value NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.raw_olist_order_payments (
    order_id VARCHAR,
    payment_sequential BIGINT,
    payment_type VARCHAR,
    payment_installments BIGINT,
    payment_value NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.raw_olist_order_reviews (
    review_id VARCHAR,
    order_id VARCHAR,
    review_score BIGINT,
    review_comment_title VARCHAR,
    review_comment_message VARCHAR,
    review_creation_date VARCHAR,
    review_answer_timestamp VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_olist_orders (
    order_id VARCHAR,
    customer_id VARCHAR,
    order_status VARCHAR,
    order_purchase_timestamp VARCHAR,
    order_approved_at VARCHAR,
    order_delivered_carrier_date VARCHAR,
    order_delivered_customer_date VARCHAR,
    order_estimated_delivery_date VARCHAR
);

CREATE TABLE IF NOT EXISTS public.raw_olist_products (
    product_id VARCHAR,
    product_category_name VARCHAR,
    product_name_lenght BIGINT,
    product_description_lenght BIGINT,
    product_photos_qty BIGINT,
    product_weight_g BIGINT,
    product_length_cm BIGINT,
    product_height_cm BIGINT,
    product_width_cm BIGINT
);

CREATE TABLE IF NOT EXISTS public.raw_olist_sellers (
    seller_id VARCHAR,
    seller_zip_code_prefix BIGINT,
    seller_city VARCHAR,
    seller_state VARCHAR
);

CREATE TABLE IF NOT EXISTS public.stg_customers (
    customer_id VARCHAR,
    customer_unique_id VARCHAR,
    zip_code_prefix VARCHAR,
    customer_city VARCHAR,
    customer_state VARCHAR
);

CREATE TABLE IF NOT EXISTS public.stg_order_items (
    order_id VARCHAR,
    order_item_id BIGINT,
    product_id VARCHAR,
    seller_id VARCHAR,
    shipping_limit_timestamp VARCHAR,
    item_price NUMERIC(15, 4),
    freight_value NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.stg_orders (
    order_id VARCHAR,
    customer_id VARCHAR,
    order_status VARCHAR,
    purchase_timestamp VARCHAR,
    approved_at VARCHAR,
    delivered_carrier_at VARCHAR,
    delivered_customer_at VARCHAR,
    estimated_delivery_at VARCHAR
);

CREATE TABLE IF NOT EXISTS public.stg_payments (
    order_id VARCHAR,
    payment_sequential BIGINT,
    payment_type VARCHAR,
    payment_installments BIGINT,
    payment_amount NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.stg_products (
    product_id VARCHAR,
    category_portuguese VARCHAR,
    category_english VARCHAR,
    name_char_length BIGINT,
    description_char_length BIGINT,
    photos_count BIGINT,
    weight_g NUMERIC(15, 4),
    length_cm NUMERIC(15, 4),
    height_cm NUMERIC(15, 4),
    width_cm NUMERIC(15, 4),
    volume_cm3 NUMERIC(15, 4)
);

CREATE TABLE IF NOT EXISTS public.stg_reviews (
    review_id VARCHAR,
    order_id VARCHAR,
    review_score BIGINT,
    review_title VARCHAR,
    review_comment VARCHAR,
    review_created_at VARCHAR,
    review_answered_at VARCHAR
);

CREATE TABLE IF NOT EXISTS public.stg_sellers (
    seller_id VARCHAR,
    zip_code_prefix VARCHAR,
    seller_city VARCHAR,
    seller_state VARCHAR
);