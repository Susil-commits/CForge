"""Generate data/gold_labels.csv containing 180+ hand-labeled ground-truth column definitions."""

import csv
from pathlib import Path
from cforge.config import GOLD_LABELS_PATH

LABELS = [
    # raw_olist_customers
    ("raw_olist_customers", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "Unique key assigned per order to identify the purchasing customer transaction.", "Customer Identifier"),
    ("raw_olist_customers", "customer_unique_id", "VARCHAR", True, "CUSTOMER_ID", "Permanent identifier representing the actual individual person across repeated purchases.", "Customer Master ID"),
    ("raw_olist_customers", "customer_zip_code_prefix", "VARCHAR", True, "POSTAL_CODE", "First 5 digits of the Brazilian CEP postal code for the customer's billing/delivery location.", "Postal Code"),
    ("raw_olist_customers", "customer_city", "VARCHAR", False, "NONE", "City name where the purchasing customer is domiciled.", "City Name"),
    ("raw_olist_customers", "customer_state", "VARCHAR", False, "NONE", "Two-letter state acronym of the purchasing customer's Brazilian federative unit.", "State Code"),

    # raw_olist_orders
    ("raw_olist_orders", "order_id", "VARCHAR", False, "NONE", "Primary transactional key identifying a single customer purchase event.", "Order Identifier"),
    ("raw_olist_orders", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "Foreign key pointing to the individual customer account that placed the purchase order.", "Customer Identifier"),
    ("raw_olist_orders", "order_status", "VARCHAR", False, "NONE", "Fulfillment lifecycle state of the order (delivered, shipped, canceled, invoiced).", "Order Status"),
    ("raw_olist_orders", "order_purchase_timestamp", "TIMESTAMP", False, "NONE", "Timestamp when the customer confirmed and submitted checkout on the marketplace.", "Purchase Timestamp"),
    ("raw_olist_orders", "order_approved_at", "TIMESTAMP", False, "NONE", "Timestamp when the payment gateway approved payment authorization.", "Payment Approval Time"),
    ("raw_olist_orders", "order_delivered_carrier_date", "TIMESTAMP", False, "NONE", "Timestamp when the seller handed off parcel to the carrier logistics partner.", "Carrier Handoff Time"),
    ("raw_olist_orders", "order_delivered_customer_date", "TIMESTAMP", False, "NONE", "Actual timestamp when the package was successfully delivered to customer doorstep.", "Customer Delivery Time"),
    ("raw_olist_orders", "order_estimated_delivery_date", "TIMESTAMP", False, "NONE", "Promised SLA estimated delivery date displayed to customer at checkout.", "Estimated Delivery SLA"),

    # raw_olist_order_items
    ("raw_olist_order_items", "order_id", "VARCHAR", False, "NONE", "Reference foreign key identifying the parent order.", "Order Identifier"),
    ("raw_olist_order_items", "order_item_id", "INTEGER", False, "NONE", "Sequential line number identifying each product item within the same order.", "Order Line Item Number"),
    ("raw_olist_order_items", "product_id", "VARCHAR", False, "NONE", "Catalog identifier of the merchandise item sold.", "Product Identifier"),
    ("raw_olist_order_items", "seller_id", "VARCHAR", False, "NONE", "Unique identifier of the third-party merchant selling the item.", "Seller Identifier"),
    ("raw_olist_order_items", "shipping_limit_date", "TIMESTAMP", False, "NONE", "Deadline timestamp by which merchant must fulfill and register package with carrier.", "Fulfillment SLA Deadline"),
    ("raw_olist_order_items", "price", "DOUBLE", False, "NONE", "Base merchandise selling price in Brazilian Real (BRL) excluding freight.", "Item Price"),
    ("raw_olist_order_items", "freight_value", "DOUBLE", False, "NONE", "Shipping logistics freight charge billed for transporting the item.", "Freight Charge"),

    # raw_olist_order_payments
    ("raw_olist_order_payments", "order_id", "VARCHAR", False, "NONE", "Foreign key linking payment record to marketplace order.", "Order Identifier"),
    ("raw_olist_order_payments", "payment_sequential", "INTEGER", False, "NONE", "Sequence sequence index when an order is settled with split payment methods.", "Payment Sequence"),
    ("raw_olist_order_payments", "payment_type", "VARCHAR", True, "FINANCIAL", "Payment method instrument used: credit_card, boleto, voucher, or debit_card.", "Payment Instrument Type"),
    ("raw_olist_order_payments", "payment_installments", "INTEGER", False, "NONE", "Number of installment installments chosen by cardholder for financing.", "Installment Count"),
    ("raw_olist_order_payments", "payment_value", "DOUBLE", True, "FINANCIAL", "Total monetary amount charged on this specific payment transaction.", "Payment Monetary Amount"),

    # raw_olist_order_reviews
    ("raw_olist_order_reviews", "review_id", "VARCHAR", False, "NONE", "Unique identifier assigned to a customer feedback review submission.", "Review Identifier"),
    ("raw_olist_order_reviews", "order_id", "VARCHAR", False, "NONE", "Order identifier for which feedback was submitted.", "Order Identifier"),
    ("raw_olist_order_reviews", "review_score", "INTEGER", False, "NONE", "Satisfaction rating awarded by customer on a scale from 1 (terrible) to 5 (excellent).", "Customer CSAT Score"),
    ("raw_olist_order_reviews", "review_comment_title", "VARCHAR", False, "NONE", "Subject line title written by customer in review form.", "Feedback Headline"),
    ("raw_olist_order_reviews", "review_comment_message", "VARCHAR", True, "CONFIDENTIAL_NOTES", "Free-form text written by customer describing fulfillment experience or grievances.", "Customer Freeform Comment"),
    ("raw_olist_order_reviews", "review_creation_date", "TIMESTAMP", False, "NONE", "Timestamp when the review invitation survey was generated.", "Review Survey Timestamp"),
    ("raw_olist_order_reviews", "review_answer_timestamp", "TIMESTAMP", False, "NONE", "Timestamp when customer completed and submitted the feedback survey.", "Review Submission Timestamp"),

    # raw_olist_products
    ("raw_olist_products", "product_id", "VARCHAR", False, "NONE", "Unique product catalog SKU code.", "Product Identifier"),
    ("raw_olist_products", "product_category_name", "VARCHAR", False, "NONE", "Category classification in Portuguese language.", "Merchandise Category"),
    ("raw_olist_products", "product_name_lenght", "INTEGER", False, "NONE", "Number of characters in the product title.", "Title Length Metric"),
    ("raw_olist_products", "product_description_lenght", "INTEGER", False, "NONE", "Character count of product description body.", "Description Length Metric"),
    ("raw_olist_products", "product_photos_qty", "INTEGER", False, "NONE", "Number of product photos published in catalog listing.", "Listing Photo Count"),
    ("raw_olist_products", "product_weight_g", "DOUBLE", False, "NONE", "Physical weight of the packaged product in grams.", "Gross Weight Grams"),
    ("raw_olist_products", "product_length_cm", "DOUBLE", False, "NONE", "Package depth/length in centimeters.", "Package Length CM"),
    ("raw_olist_products", "product_height_cm", "DOUBLE", False, "NONE", "Package height in centimeters.", "Package Height CM"),
    ("raw_olist_products", "product_width_cm", "DOUBLE", False, "NONE", "Package width in centimeters.", "Package Width CM"),

    # raw_olist_sellers
    ("raw_olist_sellers", "seller_id", "VARCHAR", False, "NONE", "Unique merchant seller ID on marketplace.", "Seller Identifier"),
    ("raw_olist_sellers", "seller_zip_code_prefix", "VARCHAR", True, "POSTAL_CODE", "Postal CEP code where the merchant fulfillment warehouse operates.", "Seller Postal Code"),
    ("raw_olist_sellers", "seller_city", "VARCHAR", False, "NONE", "City location of seller warehouse.", "Warehouse City"),
    ("raw_olist_sellers", "seller_state", "VARCHAR", False, "NONE", "Federative state unit of merchant operation.", "State Code"),

    # raw_olist_geolocation
    ("raw_olist_geolocation", "geolocation_zip_code_prefix", "VARCHAR", True, "POSTAL_CODE", "Zip code prefix mapped to geographic coordinates.", "Postal Code"),
    ("raw_olist_geolocation", "geolocation_lat", "DOUBLE", False, "NONE", "Latitude coordinate in decimal degrees.", "Geographic Latitude"),
    ("raw_olist_geolocation", "geolocation_lng", "DOUBLE", False, "NONE", "Longitude coordinate in decimal degrees.", "Geographic Longitude"),
    ("raw_olist_geolocation", "geolocation_city", "VARCHAR", False, "NONE", "City municipality name.", "City Name"),
    ("raw_olist_geolocation", "geolocation_state", "VARCHAR", False, "NONE", "State federative abbreviation.", "State Code"),

    # raw_olist_category_translation
    ("raw_olist_category_translation", "product_category_name", "VARCHAR", False, "NONE", "Portuguese category name.", "Merchandise Category"),
    ("raw_olist_category_translation", "product_category_name_english", "VARCHAR", False, "NONE", "English standardized taxonomy category translation.", "Taxonomy English Category"),

    # raw_nw_customers
    ("raw_nw_customers", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "5-character enterprise customer business account code.", "Customer Account Key"),
    ("raw_nw_customers", "company_name", "VARCHAR", False, "NONE", "Official legal business entity name of the B2B client company.", "Client Corporate Name"),
    ("raw_nw_customers", "contact_name", "VARCHAR", True, "PERSON_NAME", "Full legal name of the designated primary commercial contact individual.", "Personal Contact Name"),
    ("raw_nw_customers", "contact_title", "VARCHAR", False, "NONE", "Job title and corporate role of contact person.", "Contact Job Title"),
    ("raw_nw_customers", "address", "VARCHAR", True, "PHYSICAL_ADDRESS", "Street level physical postal address of customer headquarters.", "Physical Street Address"),
    ("raw_nw_customers", "city", "VARCHAR", False, "NONE", "Municipality where customer headquarters is located.", "City Name"),
    ("raw_nw_customers", "region", "VARCHAR", False, "NONE", "State, district or administrative province of client.", "Administrative Region"),
    ("raw_nw_customers", "postal_code", "VARCHAR", True, "POSTAL_CODE", "Postal or ZIP code of corporate billing location.", "Postal Code"),
    ("raw_nw_customers", "country", "VARCHAR", False, "NONE", "Sovereign nation state of customer entity.", "Country Name"),
    ("raw_nw_customers", "phone", "VARCHAR", True, "PHONE_NUMBER", "Direct telephone phone number for corporate communications.", "Telephone Contact"),
    ("raw_nw_customers", "fax", "VARCHAR", True, "PHONE_NUMBER", "Facsimile telephone line number for document transmission.", "Fax Number"),

    # raw_nw_orders
    ("raw_nw_orders", "order_id", "INTEGER", False, "NONE", "Numeric transaction sequence number for wholesale purchase orders.", "Order Identifier"),
    ("raw_nw_orders", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "Foreign key referencing corporate buyer account.", "Customer Account Key"),
    ("raw_nw_orders", "employee_id", "INTEGER", False, "NONE", "Identifier of the account executive who closed the order.", "Sales Representative ID"),
    ("raw_nw_orders", "order_date", "DATE", False, "NONE", "Date when the sales purchase order was executed.", "Order Creation Date"),
    ("raw_nw_orders", "required_date", "DATE", False, "NONE", "Customer requested delivery deadline date.", "Requested Delivery Date"),
    ("raw_nw_orders", "shipped_date", "DATE", False, "NONE", "Date when order cargo left dispatch facility.", "Dispatch Date"),
    ("raw_nw_orders", "ship_via", "INTEGER", False, "NONE", "Foreign identifier of maritime/freight carrier provider.", "Logistics Shipper ID"),
    ("raw_nw_orders", "freight", "DOUBLE", False, "NONE", "Monetary carrier freight tariff invoiced.", "Freight Tariff Amount"),
    ("raw_nw_orders", "ship_name", "VARCHAR", True, "PERSON_NAME", "Recipient name or destination company receiving freight cargo.", "Consignee Name"),
    ("raw_nw_orders", "ship_address", "VARCHAR", True, "PHYSICAL_ADDRESS", "Delivery delivery destination street address for freight drop-off.", "Destination Street Address"),
    ("raw_nw_orders", "ship_city", "VARCHAR", False, "NONE", "Destination city where cargo is delivered.", "Delivery City"),
    ("raw_nw_orders", "ship_region", "VARCHAR", False, "NONE", "Destination state or province.", "Delivery Region"),
    ("raw_nw_orders", "ship_postal_code", "VARCHAR", True, "POSTAL_CODE", "Destination postal routing code for shipment.", "Postal Code"),
    ("raw_nw_orders", "ship_country", "VARCHAR", False, "NONE", "Destination sovereign nation for customs clearing.", "Destination Country"),

    # raw_nw_order_details
    ("raw_nw_order_details", "order_id", "INTEGER", False, "NONE", "Wholesale order identifier reference.", "Order Identifier"),
    ("raw_nw_order_details", "product_id", "INTEGER", False, "NONE", "Wholesale product SKU identifier.", "Product Identifier"),
    ("raw_nw_order_details", "unit_price", "DOUBLE", False, "NONE", "Contracted unit price agreed for this order line item.", "Unit Price"),
    ("raw_nw_order_details", "quantity", "INTEGER", False, "NONE", "Number of units purchased in line item.", "Order Line Quantity"),
    ("raw_nw_order_details", "discount", "DOUBLE", False, "NONE", "Percentage discount applied to line item contract price.", "Discount Rate"),

    # raw_nw_products
    ("raw_nw_products", "product_id", "INTEGER", False, "NONE", "Primary key for wholesale catalog product inventory.", "Product Identifier"),
    ("raw_nw_products", "product_name", "VARCHAR", False, "NONE", "Commercial catalog trade name of merchandise.", "Product Name"),
    ("raw_nw_products", "supplier_id", "INTEGER", False, "NONE", "Foreign key linking manufacturer wholesale supplier.", "Supplier Identifier"),
    ("raw_nw_products", "category_id", "INTEGER", False, "NONE", "Foreign key pointing to product family taxonomy.", "Category Identifier"),
    ("raw_nw_products", "quantity_per_unit", "VARCHAR", False, "NONE", "Packaging description and count per wholesale container.", "Packaging Specification"),
    ("raw_nw_products", "unit_price", "DOUBLE", False, "NONE", "Standard list wholesale price per unit.", "Unit Price"),
    ("raw_nw_products", "units_in_stock", "INTEGER", False, "NONE", "Current count of available units in warehouse storage.", "Inventory Stock Count"),
    ("raw_nw_products", "units_on_order", "INTEGER", False, "NONE", "Number of units pending incoming replenishment.", "On-Order Replenishment"),
    ("raw_nw_products", "reorder_level", "INTEGER", False, "NONE", "Inventory safety stock threshold triggering new supplier PO.", "Reorder Threshold"),
    ("raw_nw_products", "discontinued", "INTEGER", False, "NONE", "Binary indicator (1=true, 0=false) whether item is terminated.", "Discontinued Flag"),

    # raw_nw_categories
    ("raw_nw_categories", "category_id", "INTEGER", False, "NONE", "Primary identifier for product family category.", "Category Identifier"),
    ("raw_nw_categories", "category_name", "VARCHAR", False, "NONE", "Short name of commodity class (e.g. Beverages, Condiments).", "Category Name"),
    ("raw_nw_categories", "description", "VARCHAR", False, "NONE", "Detailed descriptive narrative of food products in category.", "Category Description"),

    # raw_nw_employees
    ("raw_nw_employees", "employee_id", "INTEGER", False, "NONE", "Internal employee HR identification number.", "Employee Identifier"),
    ("raw_nw_employees", "last_name", "VARCHAR", True, "PERSON_NAME", "Family surname of internal corporate staff member.", "Surname"),
    ("raw_nw_employees", "first_name", "VARCHAR", True, "PERSON_NAME", "Given first personal name of employee.", "Given Name"),
    ("raw_nw_employees", "title", "VARCHAR", False, "NONE", "Official organizational corporate title.", "Job Title"),
    ("raw_nw_employees", "birth_date", "DATE", True, "CONFIDENTIAL_NOTES", "Date of birth of the employee stored for HR compliance.", "Date of Birth"),
    ("raw_nw_employees", "hire_date", "DATE", False, "NONE", "Date when employee entered payroll contract.", "Hire Date"),
    ("raw_nw_employees", "address", "VARCHAR", True, "PHYSICAL_ADDRESS", "Private residential street address of the employee.", "Home Address"),
    ("raw_nw_employees", "city", "VARCHAR", False, "NONE", "City where employee resides.", "Residential City"),
    ("raw_nw_employees", "postal_code", "VARCHAR", True, "POSTAL_CODE", "Postal code of employee personal residence.", "Postal Code"),
    ("raw_nw_employees", "country", "VARCHAR", False, "NONE", "Country where staff member resides.", "Country Name"),
    ("raw_nw_employees", "home_phone", "VARCHAR", True, "PHONE_NUMBER", "Personal landline/mobile telephone contact for employee.", "Home Phone"),
    ("raw_nw_employees", "extension", "VARCHAR", False, "NONE", "Internal PBX desk phone extension.", "Office Extension"),
    ("raw_nw_employees", "notes", "VARCHAR", True, "CONFIDENTIAL_NOTES", "Internal HR performance and educational appraisal notes.", "HR Appraisal Notes"),

    # raw_nw_shippers
    ("raw_nw_shippers", "shipper_id", "INTEGER", False, "NONE", "Primary key for shipping logistics carrier.", "Logistics Shipper ID"),
    ("raw_nw_shippers", "company_name", "VARCHAR", False, "NONE", "Commercial brand name of freight transport company.", "Freight Carrier Name"),
    ("raw_nw_shippers", "phone", "VARCHAR", True, "PHONE_NUMBER", "Dispatch customer support telephone line.", "Dispatch Phone"),

    # raw_nw_suppliers
    ("raw_nw_suppliers", "supplier_id", "INTEGER", False, "NONE", "Vendor supplier identifier.", "Supplier Identifier"),
    ("raw_nw_suppliers", "company_name", "VARCHAR", False, "NONE", "Corporate vendor company name.", "Supplier Company Name"),
    ("raw_nw_suppliers", "contact_name", "VARCHAR", True, "PERSON_NAME", "Personal name of vendor sales account manager.", "Personal Contact Name"),
    ("raw_nw_suppliers", "contact_title", "VARCHAR", False, "NONE", "Corporate role of account representative.", "Contact Job Title"),
    ("raw_nw_suppliers", "address", "VARCHAR", True, "PHYSICAL_ADDRESS", "Headquarters factory street address.", "Physical Street Address"),
    ("raw_nw_suppliers", "city", "VARCHAR", False, "NONE", "Supplier city location.", "City Name"),
    ("raw_nw_suppliers", "region", "VARCHAR", False, "NONE", "State or administrative district.", "Administrative Region"),
    ("raw_nw_suppliers", "postal_code", "VARCHAR", True, "POSTAL_CODE", "Postal code for supplier location.", "Postal Code"),
    ("raw_nw_suppliers", "country", "VARCHAR", False, "NONE", "Country of manufacture.", "Country Name"),
    ("raw_nw_suppliers", "phone", "VARCHAR", True, "PHONE_NUMBER", "Direct supplier switchboard phone number.", "Telephone Contact"),
    ("raw_nw_suppliers", "fax", "VARCHAR", True, "PHONE_NUMBER", "Supplier facsimile transmission number.", "Fax Number"),
    ("raw_nw_suppliers", "home_page", "VARCHAR", False, "NONE", "Corporate website URL link.", "Website URL"),

    # stg_customers
    ("stg_customers", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "Cleaned transactional order-level customer identifier.", "Customer Identifier"),
    ("stg_customers", "customer_unique_id", "VARCHAR", True, "CUSTOMER_ID", "Cleaned persistent individual identity token.", "Customer Master ID"),
    ("stg_customers", "zip_code_prefix", "VARCHAR", True, "POSTAL_CODE", "Standardized 5-digit postal prefix.", "Postal Code"),
    ("stg_customers", "customer_city", "VARCHAR", False, "NONE", "Standardized lowercase city name.", "City Name"),
    ("stg_customers", "customer_state", "VARCHAR", False, "NONE", "Standardized uppercase 2-letter state code.", "State Code"),

    # stg_orders
    ("stg_orders", "order_id", "VARCHAR", False, "NONE", "Normalized marketplace order primary key.", "Order Identifier"),
    ("stg_orders", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "Foreign key linking order to customer profile.", "Customer Identifier"),
    ("stg_orders", "order_status", "VARCHAR", False, "NONE", "Normalized order state string.", "Order Status"),
    ("stg_orders", "purchase_timestamp", "TIMESTAMP", False, "NONE", "Parsed UTC purchase timestamp.", "Purchase Timestamp"),
    ("stg_orders", "approved_at", "TIMESTAMP", False, "NONE", "Parsed UTC payment confirmation timestamp.", "Payment Approval Time"),
    ("stg_orders", "delivered_carrier_at", "TIMESTAMP", False, "NONE", "Parsed logistics handoff timestamp.", "Carrier Handoff Time"),
    ("stg_orders", "delivered_customer_at", "TIMESTAMP", False, "NONE", "Parsed actual final delivery timestamp.", "Customer Delivery Time"),
    ("stg_orders", "estimated_delivery_at", "TIMESTAMP", False, "NONE", "Parsed estimated delivery SLA deadline.", "Estimated Delivery SLA"),

    # stg_order_items
    ("stg_order_items", "order_id", "VARCHAR", False, "NONE", "Order identifier reference.", "Order Identifier"),
    ("stg_order_items", "order_item_id", "INTEGER", False, "NONE", "Sequential line item number.", "Order Line Item Number"),
    ("stg_order_items", "product_id", "VARCHAR", False, "NONE", "Product SKU catalog reference.", "Product Identifier"),
    ("stg_order_items", "seller_id", "VARCHAR", False, "NONE", "Seller merchant identifier.", "Seller Identifier"),
    ("stg_order_items", "shipping_limit_timestamp", "TIMESTAMP", False, "NONE", "Timestamp deadline for merchant fulfillment.", "Fulfillment SLA Deadline"),
    ("stg_order_items", "item_price", "DOUBLE", False, "NONE", "Selling price in BRL.", "Item Price"),
    ("stg_order_items", "freight_value", "DOUBLE", False, "NONE", "Allocated freight shipping fee.", "Freight Charge"),

    # stg_payments
    ("stg_payments", "order_id", "VARCHAR", False, "NONE", "Order identifier reference.", "Order Identifier"),
    ("stg_payments", "payment_sequential", "INTEGER", False, "NONE", "Sequence index for multiple payments.", "Payment Sequence"),
    ("stg_payments", "payment_type", "VARCHAR", True, "FINANCIAL", "Classified payment instrument type.", "Payment Instrument Type"),
    ("stg_payments", "payment_installments", "INTEGER", False, "NONE", "Number of installment tranches.", "Installment Count"),
    ("stg_payments", "payment_amount", "DOUBLE", True, "FINANCIAL", "Monetary value settled.", "Payment Monetary Amount"),

    # stg_products
    ("stg_products", "product_id", "VARCHAR", False, "NONE", "Product catalog SKU key.", "Product Identifier"),
    ("stg_products", "category_portuguese", "VARCHAR", False, "NONE", "Original raw category name.", "Merchandise Category"),
    ("stg_products", "category_english", "VARCHAR", False, "NONE", "Cleaned English category translation.", "Taxonomy English Category"),
    ("stg_products", "name_char_length", "INTEGER", False, "NONE", "Product title length count.", "Title Length Metric"),
    ("stg_products", "description_char_length", "INTEGER", False, "NONE", "Product description length count.", "Description Length Metric"),
    ("stg_products", "photos_count", "INTEGER", False, "NONE", "Number of catalog images.", "Listing Photo Count"),
    ("stg_products", "weight_g", "DOUBLE", False, "NONE", "Product weight in grams.", "Gross Weight Grams"),
    ("stg_products", "length_cm", "DOUBLE", False, "NONE", "Package length in cm.", "Package Length CM"),
    ("stg_products", "height_cm", "DOUBLE", False, "NONE", "Package height in cm.", "Package Height CM"),
    ("stg_products", "width_cm", "DOUBLE", False, "NONE", "Package width in cm.", "Package Width CM"),
    ("stg_products", "volume_cm3", "DOUBLE", False, "NONE", "Calculated cubic package volume in cm³.", "Package Volume CM3"),

    # stg_sellers
    ("stg_sellers", "seller_id", "VARCHAR", False, "NONE", "Merchant seller identifier.", "Seller Identifier"),
    ("stg_sellers", "zip_code_prefix", "VARCHAR", True, "POSTAL_CODE", "Fulfillment warehouse postal code.", "Seller Postal Code"),
    ("stg_sellers", "seller_city", "VARCHAR", False, "NONE", "Fulfillment warehouse city.", "Warehouse City"),
    ("stg_sellers", "seller_state", "VARCHAR", False, "NONE", "Fulfillment warehouse state.", "State Code"),

    # stg_reviews
    ("stg_reviews", "review_id", "VARCHAR", False, "NONE", "Customer review key.", "Review Identifier"),
    ("stg_reviews", "order_id", "VARCHAR", False, "NONE", "Related order reference.", "Order Identifier"),
    ("stg_reviews", "review_score", "INTEGER", False, "NONE", "Customer rating from 1 to 5.", "Customer CSAT Score"),
    ("stg_reviews", "review_title", "VARCHAR", False, "NONE", "Headline of review.", "Feedback Headline"),
    ("stg_reviews", "review_comment", "VARCHAR", True, "CONFIDENTIAL_NOTES", "Text feedback comment by customer.", "Customer Freeform Comment"),
    ("stg_reviews", "review_created_at", "TIMESTAMP", False, "NONE", "Survey timestamp.", "Review Survey Timestamp"),
    ("stg_reviews", "review_answered_at", "TIMESTAMP", False, "NONE", "Completion timestamp.", "Review Submission Timestamp"),

    # dim_customers
    ("dim_customers", "customer_unique_id", "VARCHAR", True, "CUSTOMER_ID", "Core unique customer identity key.", "Customer Master ID"),
    ("dim_customers", "primary_city", "VARCHAR", False, "NONE", "Primary domicile city.", "City Name"),
    ("dim_customers", "primary_state", "VARCHAR", False, "NONE", "Primary federative state.", "State Code"),
    ("dim_customers", "primary_zip", "VARCHAR", True, "POSTAL_CODE", "Primary postal delivery code.", "Postal Code"),
    ("dim_customers", "total_orders_placed", "BIGINT", False, "NONE", "Lifetime count of orders placed.", "Lifetime Order Count"),
    ("dim_customers", "first_order_date", "TIMESTAMP", False, "NONE", "Timestamp of initial acquisition order.", "Acquisition Date"),
    ("dim_customers", "latest_order_date", "TIMESTAMP", False, "NONE", "Timestamp of most recent customer order.", "Last Activity Date"),
    ("dim_customers", "buyer_type", "VARCHAR", False, "NONE", "Customer retention segment: repeat_buyer or single_buyer.", "Retention Segment"),

    # dim_products
    ("dim_products", "product_id", "VARCHAR", False, "NONE", "Product master SKU identifier.", "Product Identifier"),
    ("dim_products", "product_category", "VARCHAR", False, "NONE", "Standardized English category taxonomy.", "Taxonomy English Category"),
    ("dim_products", "raw_category_name", "VARCHAR", False, "NONE", "Original source language category tag.", "Merchandise Category"),
    ("dim_products", "product_weight_grams", "DOUBLE", False, "NONE", "Product mass in grams.", "Gross Weight Grams"),
    ("dim_products", "product_volume_cm3", "DOUBLE", False, "NONE", "Cubic volume in cm³.", "Package Volume CM3"),
    ("dim_products", "catalog_photo_count", "INTEGER", False, "NONE", "Count of images in catalog showcase.", "Listing Photo Count"),
    ("dim_products", "weight_class", "VARCHAR", False, "NONE", "Logistics classification: lightweight, medium_weight, heavyweight.", "Weight Logistics Class"),

    # dim_sellers
    ("dim_sellers", "seller_id", "VARCHAR", False, "NONE", "Merchant seller identifier.", "Seller Identifier"),
    ("dim_sellers", "seller_city", "VARCHAR", False, "NONE", "Seller municipality.", "Warehouse City"),
    ("dim_sellers", "seller_state", "VARCHAR", False, "NONE", "Seller state federative unit.", "State Code"),
    ("dim_sellers", "seller_zip", "VARCHAR", True, "POSTAL_CODE", "Warehouse postal code.", "Seller Postal Code"),
    ("dim_sellers", "total_items_sold", "BIGINT", False, "NONE", "Cumulative count of items fulfilled.", "Units Sold Metric"),
    ("dim_sellers", "total_revenue_brl", "DOUBLE", False, "NONE", "Total gross revenue generated in BRL.", "Gross Revenue Metric"),
    ("dim_sellers", "average_ticket_brl", "DOUBLE", False, "NONE", "Average item selling price.", "Average Item Ticket"),
    ("dim_sellers", "seller_tier", "VARCHAR", False, "NONE", "Commercial tiering (tier_1_top_seller, tier_2_growth_seller, tier_3_standard_seller).", "Seller Tier Classification"),

    # fct_orders
    ("fct_orders", "order_id", "VARCHAR", False, "NONE", "Order primary transaction identifier.", "Order Identifier"),
    ("fct_orders", "customer_id", "VARCHAR", True, "CUSTOMER_ID", "Transactional customer identifier.", "Customer Identifier"),
    ("fct_orders", "customer_unique_id", "VARCHAR", True, "CUSTOMER_ID", "Persistent customer identity token.", "Customer Master ID"),
    ("fct_orders", "customer_state", "VARCHAR", False, "NONE", "Destination state code.", "State Code"),
    ("fct_orders", "customer_city", "VARCHAR", False, "NONE", "Destination municipality.", "City Name"),
    ("fct_orders", "order_status", "VARCHAR", False, "NONE", "Order lifecycle state.", "Order Status"),
    ("fct_orders", "purchase_timestamp", "TIMESTAMP", False, "NONE", "Checkout purchase timestamp.", "Purchase Timestamp"),
    ("fct_orders", "approved_at", "TIMESTAMP", False, "NONE", "Payment verification timestamp.", "Payment Approval Time"),
    ("fct_orders", "delivered_customer_at", "TIMESTAMP", False, "NONE", "Delivered to doorstep timestamp.", "Customer Delivery Time"),
    ("fct_orders", "estimated_delivery_at", "TIMESTAMP", False, "NONE", "Estimated delivery SLA timestamp.", "Estimated Delivery SLA"),
    ("fct_orders", "total_order_items", "BIGINT", False, "NONE", "Total count of items in this order.", "Order Line Quantity"),
    ("fct_orders", "distinct_products_count", "BIGINT", False, "NONE", "Number of distinct SKUs purchased.", "Unique Products Count"),
    ("fct_orders", "merchandise_total_brl", "DOUBLE", False, "NONE", "Net merchandise basket subtotal in BRL.", "Merchandise Subtotal"),
    ("fct_orders", "freight_total_brl", "DOUBLE", False, "NONE", "Total shipping freight amount in BRL.", "Freight Charge"),
    ("fct_orders", "grand_total_brl", "DOUBLE", False, "NONE", "Total invoice amount (merchandise + freight) in BRL.", "Order Grand Total"),
    ("fct_orders", "customer_review_score", "DOUBLE", False, "NONE", "Average CSAT review rating awarded for this order.", "Customer CSAT Score"),
    ("fct_orders", "is_delayed_delivery", "BOOLEAN", False, "NONE", "Boolean flag indicating whether delivery exceeded estimated SLA.", "Delivery Delay Flag"),

    # fct_order_payments
    ("fct_order_payments", "order_id", "VARCHAR", False, "NONE", "Order transaction identifier.", "Order Identifier"),
    ("fct_order_payments", "payment_sequential", "INTEGER", False, "NONE", "Payment slice index.", "Payment Sequence"),
    ("fct_order_payments", "payment_type", "VARCHAR", True, "FINANCIAL", "Payment method instrument.", "Payment Instrument Type"),
    ("fct_order_payments", "payment_installments", "INTEGER", False, "NONE", "Financing installments count.", "Installment Count"),
    ("fct_order_payments", "payment_amount", "DOUBLE", True, "FINANCIAL", "Settled transaction amount in BRL.", "Payment Monetary Amount"),
    ("fct_order_payments", "is_credit_card_payment", "BOOLEAN", False, "NONE", "Boolean flag indicating credit card transaction.", "Credit Card Flag"),
    ("fct_order_payments", "is_split_installment", "BOOLEAN", False, "NONE", "Boolean flag indicating multi-installment financing.", "Installment Split Flag"),

    # customer_ltv
    ("customer_ltv", "customer_unique_id", "VARCHAR", True, "CUSTOMER_ID", "Core unique customer identity key.", "Customer Master ID"),
    ("customer_ltv", "primary_city", "VARCHAR", False, "NONE", "Primary customer residence city.", "City Name"),
    ("customer_ltv", "primary_state", "VARCHAR", False, "NONE", "Primary customer residence state.", "State Code"),
    ("customer_ltv", "primary_zip", "VARCHAR", True, "POSTAL_CODE", "Primary customer residence zip code.", "Postal Code"),
    ("customer_ltv", "total_orders_placed", "BIGINT", False, "NONE", "Lifetime count of completed purchases.", "Lifetime Order Count"),
    ("customer_ltv", "total_lifetime_spend_brl", "DOUBLE", False, "NONE", "Cumulative monetary gross spend across all orders.", "Customer Lifetime Spend"),
    ("customer_ltv", "avg_order_ticket_brl", "DOUBLE", False, "NONE", "Mean order basket expenditure value.", "Average Order Ticket"),
    ("customer_ltv", "satisfaction_score", "DOUBLE", False, "NONE", "Mean CSAT satisfaction rating across all reviews.", "Customer CSAT Score"),
    ("customer_ltv", "first_order_date", "TIMESTAMP", False, "NONE", "Timestamp of initial customer acquisition.", "Acquisition Date"),
    ("customer_ltv", "latest_order_date", "TIMESTAMP", False, "NONE", "Timestamp of most recent purchase activity.", "Last Activity Date"),
    ("customer_ltv", "ltv_segment", "VARCHAR", False, "NONE", "Customer LTV value tier: High Value VIP, Mid Tier Core, Low Tier Standard.", "Customer Value Tier"),

    # mart_geo_performance
    ("mart_geo_performance", "state_code", "VARCHAR", False, "NONE", "State federative abbreviation code.", "State Code"),
    ("mart_geo_performance", "customer_city", "VARCHAR", False, "NONE", "City name of customer cluster.", "City Name"),
    ("mart_geo_performance", "total_orders", "BIGINT", False, "NONE", "Total order volume dispatched to this city/state.", "Order Volume Metric"),
    ("mart_geo_performance", "regional_gmv_brl", "DOUBLE", False, "NONE", "Total gross merchandise value in BRL.", "Gross Merchandise Value"),
    ("mart_geo_performance", "avg_freight_cost_brl", "DOUBLE", False, "NONE", "Average freight shipping cost per order.", "Average Freight Metric"),
    ("mart_geo_performance", "avg_regional_satisfaction", "DOUBLE", False, "NONE", "Average customer review score for deliveries in this region.", "Regional CSAT Metric"),
    ("mart_geo_performance", "delayed_orders_count", "BIGINT", False, "NONE", "Number of orders that exceeded delivery SLA deadline.", "Delayed Orders Count"),
    ("mart_geo_performance", "delay_rate_percentage", "DOUBLE", False, "NONE", "Percentage of deliveries delivered late vs total orders.", "Delivery Delay Rate")
]


def write_gold_labels() -> Path:
    """Generate the data/gold_labels.csv ground-truth artifact."""
    GOLD_LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLD_LABELS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "table_name",
            "column_name",
            "data_type",
            "is_pii",
            "pii_type",
            "true_business_description",
            "glossary_term"
        ])
        for row in LABELS:
            writer.writerow(row)
    return GOLD_LABELS_PATH


if __name__ == "__main__":
    p = write_gold_labels()
    print(f"Wrote {len(LABELS)} gold labels to {p}")
