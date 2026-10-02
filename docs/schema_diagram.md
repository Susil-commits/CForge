# ContextForge Data Estate Architecture & Schema Diagram

ContextForge models a realistic enterprise data estate composed of heterogeneous data systems:
1. **Olist Brazilian E-Commerce Estate** (High-volume B2C marketplace transactions, geo-spatial delivery data, PII customers, reviews, and payments).
2. **Northwind Wholesale Estate** (B2B wholesale trading, corporate client accounts, employees, suppliers, and shipping logistics).
3. **Multi-layer Transformation Pipeline** (Staging models -> Dimensions & Facts -> Business Marts).

---

## 1. Lineage & Transformation Topology

```mermaid
graph TD
    subgraph Raw_Olist [Olist Brazilian E-Commerce: Raw Layer]
        ROC[raw_olist_customers]
        ROO[raw_olist_orders]
        ROI[raw_olist_order_items]
        ROP[raw_olist_order_payments]
        ROR[raw_olist_order_reviews]
        ROPR[raw_olist_products]
        ROS[raw_olist_sellers]
        ROT[raw_olist_category_translation]
        ROG[raw_olist_geolocation]
    end

    subgraph Raw_Northwind [Northwind Wholesale: Raw Layer]
        NWC[raw_nw_customers]
        NWO[raw_nw_orders]
        NWD[raw_nw_order_details]
        NWP[raw_nw_products]
        NWE[raw_nw_employees]
        NWS[raw_nw_suppliers]
        NWSH[raw_nw_shippers]
        NWCA[raw_nw_categories]
    end

    subgraph Staging_Layer [ContextForge Staging Layer]
        SC[stg_customers]
        SO[stg_orders]
        SOI[stg_order_items]
        SP[stg_payments]
        SPR[stg_products]
        SS[stg_sellers]
        SR[stg_reviews]
    end

    subgraph Core_Marts [Core Dimensions & Facts]
        DC[dim_customers]
        DP[dim_products]
        DS[dim_sellers]
        FO[fct_orders]
        FOP[fct_order_payments]
    end

    subgraph Business_Marts [Business Intelligence Marts]
        LTV[customer_ltv]
        GEO[mart_geo_performance]
    end

    ROC --> SC
    ROO --> SO
    ROI --> SOI
    ROP --> SP
    ROPR --> SPR
    ROT --> SPR
    ROS --> SS
    ROR --> SR

    SC --> DC
    SO --> DC
    SPR --> DP
    SS --> DS
    SOI --> DS

    SO --> FO
    SC --> FO
    SOI --> FO
    SR --> FO

    SP --> FOP

    DC --> LTV
    FO --> LTV

    FO --> GEO
```

---

## 2. Table Schemas & Classification Highlights

### Staging Layer
- **`stg_customers`**: `customer_id` (PII), `customer_unique_id` (PII), `zip_code_prefix` (PII), `customer_city`, `customer_state`.
- **`stg_orders`**: `order_id`, `customer_id` (PII), `order_status`, `purchase_timestamp`, `approved_at`, `delivered_carrier_at`, `delivered_customer_at`, `estimated_delivery_at`.
- **`stg_order_items`**: `order_id`, `order_item_id`, `product_id`, `seller_id`, `shipping_limit_timestamp`, `item_price`, `freight_value`.
- **`stg_payments`**: `order_id`, `payment_sequential`, `payment_type` (Financial), `payment_installments`, `payment_amount` (Financial).
- **`stg_products`**: `product_id`, `category_portuguese`, `category_english`, `name_char_length`, `description_char_length`, `photos_count`, `weight_g`, `length_cm`, `height_cm`, `width_cm`, `volume_cm3`.
- **`stg_sellers`**: `seller_id`, `zip_code_prefix` (PII), `seller_city`, `seller_state`.
- **`stg_reviews`**: `review_id`, `order_id`, `review_score`, `review_title`, `review_comment` (Confidential), `review_created_at`, `review_answered_at`.

### Marts & Analytics Layer
- **`dim_customers`**: Master customer profile entity with aggregated order counts, retention categorization (`repeat_buyer` vs `single_buyer`), and postal details.
- **`dim_products`**: Catalog dimensions enriched with logistics weight classes (`lightweight`, `medium_weight`, `heavyweight`) and cubic cm volume.
- **`dim_sellers`**: Performance tiering (`tier_1_top_seller`, `tier_2_growth_seller`, `tier_3_standard_seller`), merchandise revenue, and average tickets.
- **`fct_orders`**: Granular order lifecycle fact linking customer IDs, merchandise GMV, freight totals, delivery delay flags, and CSAT scores.
- **`fct_order_payments`**: Financial transactions, installment breakdowns, and payment method flags.
- **`customer_ltv`**: RFM analytics classifying customers into `High Value VIP`, `Mid Tier Core`, and `Low Tier Standard`.
- **`mart_geo_performance`**: Regional SLA delivery rates, freight overheads, and late order percentages by state and city.
