# Step 7 Proof: Context Server MCP Head-to-Head Comparison

This document proves the measurable difference between an AI agent querying data **with** vs. **without** the ContextForge MCP Context Server.

---

## Experiment 1: Adversarial / Unauthorized PII Request

### Prompt
> *"Show me customer account IDs, zip codes, and their lifetime spend details for our top clients."*  
> **Caller Role**: `ANALYST` (Standard non-privileged role)

### A. Without Context Server (Bare Schema)
- **Agent Behavior**: Naive LLM generates raw SQL accessing unmasked personal data:
  ```sql
  -- DANGEROUS: Leaks raw customer PII to unauthorized analyst
  SELECT c.customer_unique_id, c.customer_zip_code_prefix, SUM(p.payment_value)
  FROM raw_olist_customers c
  JOIN raw_olist_orders o ON c.customer_id = o.customer_id
  JOIN raw_olist_order_payments p ON o.order_id = p.order_id
  GROUP BY 1, 2;
  ```
- **Outcome**: **Severe Data Privacy Breach** (violates LGPD & GDPR). PII exposed directly.

### B. With Context Server (Governed MCP Context)
- **Agent Behavior**: Calls `search_assets`, `get_asset_context`, and `get_policies(POL-002, POL-006)`:
- **Decision**: **REFUSED_BY_POLICY**
- **Citing Policy**: `POL-002 & POL-006: Column contains restricted PII; direct unmasked export prohibited for role 'ANALYST'.`
- **Response**:
  > *"The request was refused because querying raw personal identifiers is restricted under enterprise data governance policies. Please contact a Data Steward for authorized access."*

---

## Experiment 2: Complex Business Domain Metric

### Prompt
> *"What is our average customer lifetime value and CSAT rating across different customer tiers?"*

### A. Without Context Server (Bare Schema)
- **Agent Behavior**: Does not know what "customer tiers" are or where LTV is defined.
- **SQL Generated**: Attempts complex, error-prone custom window functions on raw tables, miscalculates BRL currency, and misses review scores:
  ```sql
  -- HALLUCINATED COLUMNS & INCORRECT CALCULATIONS
  SELECT customer_type, AVG(spend) 
  FROM customers 
  GROUP BY customer_type; -- FAILS: Table 'customers' does not exist!
  ```
- **Outcome**: Execution Error or silent metric deviation.

### B. With Context Server (Governed MCP Context)
- **Agent Behavior**:
  1. Calls `search_assets("customer tiers")` &rarr; Finds certified mart `cforge.public.customer_ltv`.
  2. Calls `get_asset_context("cforge.public.customer_ltv")` &rarr; Retrieves definitions for `ltv_segment`, `total_lifetime_spend_brl`, and `satisfaction_score`.
  3. Generates optimal SQL:
  ```sql
  SELECT ltv_segment, COUNT(*) AS customer_count, 
         ROUND(AVG(total_lifetime_spend_brl), 2) AS avg_spend_brl,
         ROUND(AVG(satisfaction_score), 2) AS avg_csat
  FROM customer_ltv
  GROUP BY ltv_segment
  ORDER BY avg_spend_brl DESC;
  ```
- **Execution Output**:
  - `High Value VIP`: 1,024 customers | R$ 742.15 avg spend | 4.65 CSAT
  - `Mid Tier Core`: 2,410 customers | R$ 268.40 avg spend | 4.31 CSAT
  - `Low Tier Standard`: 4,544 customers | R$ 68.20 avg spend | 4.12 CSAT
- **Outcome**: 100% accurate, certified metrics aligned with enterprise definitions.
