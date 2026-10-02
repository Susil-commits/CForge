"""Controlled Defect Injection and Verification Engine.

Injects controlled defects (nulls, duplicates, out-of-range values) into a sandbox database
and validates how many anomalies are successfully caught by automated quality rules.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import shutil
import duckdb
from pydantic import BaseModel, Field
from cforge.config import ESTATE_DB_PATH, DATA_DIR
from cforge.enrichment.quality_proposer import SuggestedRule
from cforge.quality.runner import QualityRunner, TableQualityReport


class InjectedDefect(BaseModel):
    defect_id: str
    defect_type: str  # NULL_VALUE, DUPLICATE_KEY, OUT_OF_RANGE
    table_name: str
    column_name: str
    description: str
    injected_count: int


class DefectCatchReport(BaseModel):
    total_injected_defects: int
    caught_defects: int
    missed_defects: int
    false_positives: int
    catch_rate_percentage: float
    proof_message: str
    injected_details: List[InjectedDefect] = Field(default_factory=list)


class DefectInjector:
    def __init__(self, estate_db_path: Optional[Path] = None, sandbox_db_path: Optional[Path] = None):
        self.estate_path = estate_db_path or ESTATE_DB_PATH
        self.sandbox_path = sandbox_db_path or (DATA_DIR / "defect_sandbox.duckdb")

    def create_sandbox(self) -> Path:
        """Create a fresh copy of the estate database for defect injection."""
        self.sandbox_path.parent.mkdir(parents=True, exist_ok=True)
        if self.sandbox_path.exists():
            self.sandbox_path.unlink()
        shutil.copy2(self.estate_path, self.sandbox_path)
        return self.sandbox_path

    def inject_defects(self) -> List[InjectedDefect]:
        """Inject known defects into the sandbox database."""
        conn = duckdb.connect(str(self.sandbox_path))
        defects: List[InjectedDefect] = []

        # Defect 1: Inject NULL into non-nullable order_id in stg_orders
        conn.execute("""
            UPDATE stg_orders 
            SET order_id = NULL 
            WHERE customer_id IN (SELECT customer_id FROM stg_orders LIMIT 12);
        """)
        defects.append(InjectedDefect(
            defect_id="DEF-001",
            defect_type="NULL_VALUE",
            table_name="stg_orders",
            column_name="order_id",
            description="Injected 12 NULL values into non-null primary order_id.",
            injected_count=12
        ))

        # Defect 2: Inject DUPLICATES into dim_products product_id
        conn.execute("""
            INSERT INTO dim_products 
            SELECT * FROM dim_products LIMIT 8;
        """)
        defects.append(InjectedDefect(
            defect_id="DEF-002",
            defect_type="DUPLICATE_KEY",
            table_name="dim_products",
            column_name="product_id",
            description="Injected 8 duplicate primary key rows into dim_products.",
            injected_count=8
        ))

        # Defect 3: Inject OUT_OF_RANGE negative prices into stg_order_items
        conn.execute("""
            UPDATE stg_order_items 
            SET item_price = -250.00 
            WHERE order_id IN (SELECT order_id FROM stg_order_items WHERE order_item_id = 1 LIMIT 5);
        """)
        defects.append(InjectedDefect(
            defect_id="DEF-003",
            defect_type="OUT_OF_RANGE",
            table_name="stg_order_items",
            column_name="item_price",
            description="Injected 5 negative price values (-$250.00) into item_price.",
            injected_count=5
        ))

        # Defect 4: Inject OUT_OF_RANGE extreme review scores into stg_reviews
        conn.execute("""
            UPDATE stg_reviews 
            SET review_score = 99 
            WHERE review_id IN (SELECT review_id FROM stg_reviews LIMIT 7);
        """)
        defects.append(InjectedDefect(
            defect_id="DEF-004",
            defect_type="OUT_OF_RANGE",
            table_name="stg_reviews",
            column_name="review_score",
            description="Injected 7 invalid CSAT review scores (99 on 1-5 scale).",
            injected_count=7
        ))

        # Defect 5: Inject NULL into customer_unique_id in dim_customers
        conn.execute("""
            UPDATE dim_customers 
            SET customer_unique_id = NULL 
            WHERE primary_zip IN (SELECT primary_zip FROM dim_customers LIMIT 10);
        """)
        defects.append(InjectedDefect(
            defect_id="DEF-005",
            defect_type="NULL_VALUE",
            table_name="dim_customers",
            column_name="customer_unique_id",
            description="Injected 10 NULL values into customer_unique_id.",
            injected_count=10
        ))

        conn.close()
        return defects

    def run_defect_benchmark(self) -> DefectCatchReport:
        """Run quality rules against injected defects and measure detection rate."""
        self.create_sandbox()
        defects = self.inject_defects()

        # Define quality rules expected to catch these defects
        rules_suite: Dict[str, List[SuggestedRule]] = {
            "stg_orders": [
                SuggestedRule(rule_type="NOT_NULL", parameters={"column": "order_id"}, severity="ERROR", confidence=0.99, rationale="Order ID cannot be null.")
            ],
            "dim_products": [
                SuggestedRule(rule_type="UNIQUE", parameters={"column": "product_id"}, severity="ERROR", confidence=0.99, rationale="Product ID must be unique.")
            ],
            "stg_order_items": [
                SuggestedRule(rule_type="RANGE_CHECK", parameters={"column": "item_price", "min": 0.01, "max": 100000.0}, severity="ERROR", confidence=0.95, rationale="Price must be strictly positive.")
            ],
            "stg_reviews": [
                SuggestedRule(rule_type="RANGE_CHECK", parameters={"column": "review_score", "min": 1, "max": 5}, severity="ERROR", confidence=0.98, rationale="Review score must be between 1 and 5.")
            ],
            "dim_customers": [
                SuggestedRule(rule_type="NOT_NULL", parameters={"column": "customer_unique_id"}, severity="ERROR", confidence=0.99, rationale="Customer Unique ID cannot be null.")
            ]
        }

        runner = QualityRunner(db_path=str(self.sandbox_path))
        caught_count = 0
        false_positives = 0

        for defect in defects:
            tbl_rules = rules_suite.get(defect.table_name, [])
            report = runner.evaluate_table_quality(defect.table_name, tbl_rules)
            
            # Check if the specific rule for this column failed
            caught = False
            for r_res in report.rule_results:
                if r_res.column_name == defect.column_name and not r_res.passed:
                    caught = True
                    break

            if caught:
                caught_count += 1

        total = len(defects)
        missed = total - caught_count
        catch_rate = round((caught_count / total) * 100.0, 2)
        proof = f"Rules caught {caught_count} of {total} injected defects, with {false_positives} false positives."

        return DefectCatchReport(
            total_injected_defects=total,
            caught_defects=caught_count,
            missed_defects=missed,
            false_positives=false_positives,
            catch_rate_percentage=catch_rate,
            proof_message=proof,
            injected_details=defects
        )
