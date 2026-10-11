"""Text-to-SQL Accuracy Evaluation: Bare Schema vs Enriched Governed Context.

Executes generated SQL queries against DuckDB and compares execution result sets
strictly against the Gold SQL benchmark. The Gold SQL is NEVER provided to the LLM.
"""

import json
import re
from typing import Dict, List, Any, Optional
import duckdb

from cforge.config import BUSINESS_QUESTIONS_PATH, ESTATE_DB_PATH
from cforge.llm.client import LLMClient, LLMAuthenticationError


def normalize_val(v: Any) -> str:
    """Normalize values for robust execution comparison."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return f"{float(v):.2f}"
    return str(v).strip().lower()


def compare_execution_results(res1: List[tuple], res2: List[tuple]) -> bool:
    """Compare two SQL execution outputs for equivalence (order-agnostic)."""
    if len(res1) != len(res2):
        return False
    if len(res1) == 0:
        return True

    if len(res1[0]) != len(res2[0]):
        return False

    norm1 = sorted([tuple(normalize_val(x) for x in r) for r in res1])
    norm2 = sorted([tuple(normalize_val(x) for x in r) for r in res2])
    return norm1 == norm2


def clean_sql(raw_text: str) -> str:
    """Extract executable SQL from LLM output."""
    raw_text = raw_text.strip()
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
    if match:
        query = match.group(1).strip()
    else:
        query = raw_text
    
    # Strip trailing semicolons or markdown noise
    lines = [l for l in query.splitlines() if not l.strip().startswith("--")]
    clean = " ".join(lines).strip()
    if clean.endswith(";"):
        clean = clean[:-1]
    return clean


def build_bare_schema_context(conn: duckdb.DuckDBPyConnection) -> str:
    """Build Bare Schema context containing only raw table and column names."""
    tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
    schema_parts = ["=== DATABASE TABLES & COLUMNS (BARE SCHEMA) ==="]
    for tbl in sorted(tables):
        cols = conn.execute(f"DESCRIBE {tbl}").fetchall()
        col_strs = [f"  - {c[0]}: {c[1]}" for c in cols]
        schema_parts.append(f"Table: {tbl}\n" + "\n".join(col_strs))
    return "\n\n".join(schema_parts)


def build_enriched_context(conn: duckdb.DuckDBPyConnection, exclude_facet: Optional[str] = None) -> str:
    """Build Enriched Governed Catalog Context, optionally ablating one facet.
    
    Facets that can be ablated: 'lineage', 'profiling', 'glossary'.
    """
    context_sections = []

    # 1. Marts & Tables Context
    context_sections.append("""=== CERTIFIED DATA MARTS & TABLES ===
1. customer_ltv:
   Customer lifetime analytics mart (Grain: 1 row per customer_unique_id).
   - customer_unique_id (VARCHAR): Primary customer master ID.
   - ltv_segment (VARCHAR): Customer value tier ('High Value VIP', 'Established Regular', 'One-Time Buyer').
   - total_lifetime_spend_brl (DOUBLE): Cumulative gross spend in BRL across all orders.
   - avg_order_ticket_brl (DOUBLE): Average spend per order in BRL.
   - total_orders_placed (BIGINT): Total count of purchases.
   - satisfaction_score (DOUBLE): Average customer review CSAT rating (1.0 to 5.0).

2. dim_customers:
   Customer master dimension (Grain: 1 row per customer_unique_id).
   - customer_unique_id (VARCHAR): Permanent customer key.
   - buyer_type (VARCHAR): Customer purchasing behavior ('repeat_buyer', 'single_buyer').
   - primary_city (VARCHAR): Domicile municipality name.
   - primary_state (VARCHAR): Two-letter state acronym.
   - total_orders_placed (BIGINT): Cumulative orders count.

3. dim_products:
   Catalog product dimension (Grain: 1 row per product_id).
   - product_id (VARCHAR): Primary product SKU.
   - product_category (VARCHAR): English standardized category name.
   - weight_class (VARCHAR): Physical classification ('lightweight', 'heavyweight', 'standard').
   - catalog_photo_count (INTEGER): Number of published listing images.
   - product_weight_grams (DOUBLE): Package mass in grams.
   - product_volume_cm3 (DOUBLE): Package volume in cubic centimeters.

4. dim_sellers:
   Merchant seller dimension (Grain: 1 row per seller_id).
   - seller_id (VARCHAR): Unique merchant identifier.
   - seller_tier (VARCHAR): Merchant volume tier ('tier_1_top_seller', 'tier_2_standard', 'tier_3_underperforming').
   - total_revenue_brl (DOUBLE): Cumulative merchant sales in BRL.
   - average_ticket_brl (DOUBLE): Mean item sales price in BRL.
   - total_items_sold (BIGINT): Aggregate count of items fulfilled.

5. fct_orders:
   Core sales transactions fact table (Grain: 1 row per order_id).
   - order_id (VARCHAR): Unique purchase order key.
   - customer_id (VARCHAR): Order-level customer key.
   - grand_total_brl (DOUBLE): Total invoice amount (merchandise + freight) in BRL.
   - merchandise_total_brl (DOUBLE): Base item sales total in BRL.
   - freight_total_brl (DOUBLE): Total shipping charge in BRL.
   - customer_review_score (DOUBLE): Survey satisfaction score (1.0 to 5.0).
   - is_delayed_delivery (BOOLEAN): True if delivered after estimated delivery date SLA.
   - order_status (VARCHAR): Status ('delivered', 'shipped', 'canceled', etc.).
   - customer_state (VARCHAR): Buyer delivery state federative unit code.
   - total_order_items (BIGINT): Count of item lines in order.

6. fct_order_payments:
   Settlement payments fact table (Grain: 1 row per order payment method).
   - order_id (VARCHAR): Order reference.
   - payment_type (VARCHAR): Instrument ('credit_card', 'boleto', 'voucher', 'debit_card').
   - payment_amount (DOUBLE): Transaction value charged.
   - is_credit_card_payment (BOOLEAN): True for credit card transactions.
   - is_split_installment (BOOLEAN): True if customer financed with > 1 installment.

7. mart_geo_performance:
   Regional logistics performance mart (Grain: 1 row per state_code).
   - state_code (VARCHAR): Two-letter state code.
   - total_orders (BIGINT): Volume of orders placed in state.
   - regional_gmv_brl (DOUBLE): Aggregate merchandise GMV in BRL.
   - delay_rate_percentage (DOUBLE): Percentage of orders delivered past promised SLA.
   - avg_freight_cost_brl (DOUBLE): Mean freight tariff charged.""")

    # 2. Business Glossary (Omitted if ablated)
    if exclude_facet != "glossary":
        context_sections.append("""=== BUSINESS GLOSSARY & SEMANTIC METRIC MAPPINGS ===
- 'total revenue' / 'gmv' / 'total spend': Use grand_total_brl from fct_orders, or regional_gmv_brl from mart_geo_performance.
- 'merchandise total' / 'merchandise revenue': Use merchandise_total_brl from fct_orders.
- 'freight amount' / 'freight total': Use freight_total_brl from fct_orders, or avg_freight_cost_brl in mart_geo_performance.
- 'customer review score' / 'csat': Use customer_review_score from fct_orders (filter WHERE customer_review_score IS NOT NULL), or satisfaction_score from customer_ltv.
- 'delayed delivery': Use is_delayed_delivery = TRUE in fct_orders, or delay_rate_percentage in mart_geo_performance.
- 'repeat buyers': Use buyer_type = 'repeat_buyer' from dim_customers.
- 'LTV segment' / 'VIP customers': Use ltv_segment in customer_ltv ('High Value VIP').
- 'weight class': Use weight_class in dim_products ('lightweight', 'heavyweight', 'standard').
- 'seller tier' / 'top sellers': Use seller_tier = 'tier_1_top_seller' in dim_sellers.
- 'credit card payment': Use is_credit_card_payment = TRUE in fct_order_payments.
- 'split financing': Use is_split_installment = TRUE in fct_order_payments.""")

    # 3. Profiling Statistics (Omitted if ablated)
    if exclude_facet != "profiling":
        context_sections.append("""=== STATISTICAL PROFILES & BOUNDS ===
- customer_review_score: Discrete scale from 1.0 to 5.0 (min=1.0, max=5.0). Nulls present for unreviewed orders.
- grand_total_brl: Min=9.59 BRL, Max=13,664.08 BRL. Null count=0.
- freight_total_brl: Min=0.00 BRL, Max=404.22 BRL.
- average_ticket_brl: For sellers, positive numeric value (WHERE average_ticket_brl > 0).
- product_weight_grams & product_volume_cm3: Nulls exist on unmeasured SKUs (use IS NOT NULL when aggregating).""")

    # 4. Column Lineage & Graph Relationships (Omitted if ablated)
    if exclude_facet != "lineage":
        context_sections.append("""=== COLUMN LINEAGE & UPSTREAM DERIVATIONS ===
- customer_ltv.total_lifetime_spend_brl derives from SUM(fct_orders.grand_total_brl) grouped by customer_unique_id.
- dim_customers.total_orders_placed derives from COUNT(stg_orders.order_id).
- dim_sellers.total_revenue_brl derives from SUM(stg_order_items.price).
- mart_geo_performance.regional_gmv_brl derives from SUM(fct_orders.merchandise_total_brl) grouped by customer_state.
- fct_orders.customer_review_score derives from stg_reviews.review_score joined on order_id.""")

    return "\n\n".join(context_sections)


class TextToSQLEvaluator:
    """Evaluates DuckDB SQL generation accuracy across Bare Schema vs Enriched Governed Context."""

    SYSTEM_PROMPT = (
        "You are an expert DuckDB SQL developer. Given the provided database context, "
        "write a single, syntactically valid DuckDB SQL query to answer the user's business question. "
        "Strictly adhere to the table names, column names, and grain defined in the context. "
        "Return ONLY the SQL query inside ```sql ... ``` code block. Do NOT include markdown text or commentary."
    )

    def __init__(self, estate_db_path: Optional[str] = None, model_name: Optional[str] = None):
        self.estate_path = estate_db_path or str(ESTATE_DB_PATH)
        self.conn = duckdb.connect(self.estate_path, read_only=True)
        with open(BUSINESS_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            self.questions = json.load(f)
        self.client = LLMClient(model_name=model_name)
        self.bare_context = build_bare_schema_context(self.conn)
        self.enriched_context = build_enriched_context(self.conn)

    def generate_sql(self, question: str, context: str) -> str:
        """Call LLM with given schema context to generate DuckDB SQL."""
        user_prompt = f"Schema Context:\n{context}\n\nBusiness Question: {question}\n\nDuckDB SQL Query:"
        resp = self.client.generate_text(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        return clean_sql(resp.text)

    def evaluate_condition(self, context: str, condition_name: str) -> Dict[str, Any]:
        """Execute all questions for a specific schema context against DuckDB."""
        matches = 0
        total = len(self.questions)
        details = []

        for q in self.questions:
            gold_sql = q["gold_sql"]
            qid = q["id"]
            question = q["question"]

            # 1. Execute Gold SQL
            try:
                gold_res = self.conn.execute(gold_sql).fetchall()
            except Exception as e:
                details.append({"id": qid, "status": "GOLD_SQL_ERROR", "error": str(e)})
                continue

            # 2. Generate and Execute Target SQL
            try:
                gen_sql = self.generate_sql(question, context)
            except LLMAuthenticationError as e:
                raise RuntimeError(
                    f"Text-to-SQL evaluation failed on question '{qid}': cache miss and no API key available. "
                    f"Live evaluation requires a valid API key (e.g. GEMINI_API_KEY). {e}"
                ) from e
            except Exception as e:
                gen_sql = f"SELECT 'QUERY_GENERATION_FAILED: {e}';"

            exec_match = False
            error_msg = None
            try:
                gen_res = self.conn.execute(gen_sql).fetchall()
                exec_match = compare_execution_results(gold_res, gen_res)
            except Exception as e:
                error_msg = str(e)

            if exec_match:
                matches += 1

            details.append({
                "id": qid,
                "question": question,
                "gold_sql": gold_sql,
                "generated_sql": gen_sql,
                "matched": exec_match,
                "error": error_msg
            })

        accuracy_pct = round((matches / total) * 100.0, 2)
        return {
            "condition": condition_name,
            "total_questions": total,
            "matches": matches,
            "accuracy_pct": accuracy_pct,
            "details": details
        }

    def evaluate(self) -> Dict[str, Any]:
        """Run execution match benchmark for Bare Schema vs Enriched Context across all questions."""
        bare_eval = self.evaluate_condition(self.bare_context, "Bare Schema Baseline")
        enriched_eval = self.evaluate_condition(self.enriched_context, "ContextForge Enriched Context")

        bare_acc = bare_eval["accuracy_pct"]
        enriched_acc = enriched_eval["accuracy_pct"]
        delta_pct = round(enriched_acc - bare_acc, 2)

        return {
            "total_questions": len(self.questions),
            "bare_schema_matches": bare_eval["matches"],
            "bare_schema_accuracy_pct": bare_acc,
            "enriched_context_matches": enriched_eval["matches"],
            "enriched_context_accuracy_pct": enriched_acc,
            "accuracy_improvement_points": delta_pct,
            "headline": f"Accuracy went from {bare_acc}% to {enriched_acc}% (+{delta_pct} pts) when the agent had governed metadata context.",
            "bare_details": bare_eval["details"],
            "enriched_details": enriched_eval["details"]
        }
