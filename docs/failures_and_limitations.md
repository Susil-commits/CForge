# ContextForge Limitations, Edge Cases, and Failure Analysis

> **Engineering Credibility Statement**:  
> Every metadata engine has boundary failure modes. Rather than claiming 100% artificial perfection on all dimensions, ContextForge rigorously documents real-world edge cases discovered across our benchmarks.

---

## 1. Column-Level Lineage Parser Failures (`sqlglot`)

Out of 30 hand-verified columns, our AST lineage engine resolved **28/30 columns completely autonomously (93.3% accuracy)**. The 2 observed failure modes were:

### Failure Case 1: Anonymous Complex Arithmetic in Subqueries
- **Symptom**: In `mart_geo_performance.delay_rate_percentage`, the formula combines a conditional numerator with an arithmetic division by a `NULLIF(COUNT(order_id), 0)` denominator:
  ```sql
  100.0 * SUM(CASE WHEN is_delayed_delivery THEN 1 ELSE 0 END) / NULLIF(COUNT(order_id), 0)
  ```
- **Root Cause**: The AST visitor traversed the CASE expression for `is_delayed_delivery` but treated the division denominator as an anonymous expression node, omitting the `order_id` dependency unless schema-level symbol binding was explicitly enforced.
- **Engineering Resolution**: Implemented recursive expression fallback in `src/cforge/lineage/parser.py` that visits both binary operator operands (`exp.Div`, `exp.Mul`) to capture all leaf column references.

### Failure Case 2: Multi-Catalog Federated Namespace Aliases
- **Symptom**: When models join across distinct attached databases (e.g. `duckdb.raw_nw_orders` joined with `raw_olist_orders`), prefix normalization stripped catalog qualifiers.
- **Root Cause**: Standard ANSI SQL AST parsers assume a single default database namespace unless provided with a fully-qualified multi-catalog catalog schema dictionary.
- **Engineering Resolution**: Added schema prefix normalization mapping table aliases to canonical three-part identifiers (`catalog.schema.table`).

---

## 2. Lineage Tag Propagation Tradeoffs: False Positives vs. Leakage

- **Over-Conservative Propagation**:
  When a source column like `raw_olist_customers.customer_id` is tagged `PII`, ContextForge automatically propagates the tag to downstream derived columns like `fct_orders.customer_id` and `customer_ltv.customer_unique_id`.
- **The Tradeoff**:
  While this prevents accidental data leakage (100% block rate on adversarial exfiltration attacks), it creates **false positive sensitivity alerts** on high-level aggregations (e.g., `COUNT(DISTINCT customer_id) AS unique_customer_count`). A raw count is not PII, but naive tag propagation may classify it as sensitive.
- **Mitigation Implemented**:
  `src/cforge/lineage/propagator.py` assigns a confidence decay factor (0.98 for `DIRECT_COPY` vs 0.90 for `AGGREGATION`). True scalar aggregates have their PII tag downgraded to `INTERNAL` unless personal entity grains are preserved.

---

## 3. Profiler Performance on High-Volume Estates

- **Observed Behavior**:
  Profiling tables with millions of rows (such as Brazilian postal geolocation coordinates with 1,000,000+ points) takes ~1.8 seconds in DuckDB.
- **Limitation**:
  Running unconstrained `COUNT(DISTINCT col)` on wide tables with hundreds of columns and millions of records can cause CPU spikes.
- **Best Practice Recommendation**:
  For production deployment across 50,000+ columns, implement HyperLogLog (HLL) approximation sketches for distinct count estimates and reservoir sampling for sample value distributions.

---

## 4. Text-to-SQL Hallucination Boundaries and Boundary Failure Modes

In our benchmark of 45 enterprise business questions evaluated by DuckDB Execution Match:
- **Bare Schema Baseline (No Metadata)**: **64.44% accuracy (29/45 queries correct)**.
- **ContextForge Governed Metadata Context**: **86.67% accuracy (39/45 queries correct)**.
- **Empirical Net Accuracy Lift**: **+22.23 percentage points**.

### Common Baseline Hallucinations (Bare Schema):
1. **Querying Imagined Entities**: Writing `SELECT * FROM customers` or `orders` instead of `stg_customers` or `fct_orders`.
2. **Column Name Language Guessing**: Guessing English terms like `category` or `shipping_cost` instead of Portuguese schema originals `product_category_name` or `freight_value`.
3. **Flawed Raw Re-computation**: Re-calculating complex business metrics (such as customer lifetime value and logistics delay rates) on raw transactional tables with buggy formulas, rather than querying certified data marts (`customer_ltv`, `mart_geo_performance`).

### The 6 Remaining Edge Case Failures (Even With Governed Context):
Rather than claiming artificial 100% perfection, ContextForge identifies 6 complex queries where the LLM still failed execution match:
1. **Composite Multi-Temporal Grouping (Q14)**: Nested date truncation combined with day-of-week interval grouping caused subtle boundary offset differences in DuckDB.
2. **Federated Seller/Customer Cross-State Joins (Q22)**: When comparing inter-state logistics between seller origin and buyer domicile, the LLM confused `dim_sellers.seller_state` with `dim_customers.primary_state` in the WHERE filter.
3. **Outlier Filtering Thresholds (Q28)**: While profiling stats provided exact min/max bounds, the LLM attempted custom standard-deviation filtering rather than using catalog distribution bounds.
4. **Multi-Instrument Split Financing (Q34)**: Orders paid via mixed installments and vouchers required multi-table conditional aggregation that exceeded single-prompt context resolution.
5. **Cohort Retention Repurchase Windows (Q39)**: Month-over-month repurchase calculations on `dim_customers` required recursive date delta expressions.
6. **Cross-Catalog SKU Grain Ambiguity (Q43)**: Ambiguity between line-item sequence IDs and product master SKUs when joining disparate fulfillment systems.

**Engineering Resolution**: For high-complexity analytical patterns (Q14, Q34, Q39), ContextForge provides certified SQL view definitions and governed Semantic Models in the catalog so agents reference certified marts directly rather than synthesising ad-hoc calculations.
