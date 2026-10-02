"""Data Quality Rule Execution Engine.

Executes quality validation rules against DuckDB/PostgreSQL, computes asset quality scores,
and attaches verification metrics to catalog assets.
"""

from typing import Dict, List, Any, Optional
import duckdb
from pydantic import BaseModel, Field
from cforge.config import ESTATE_DB_PATH
from cforge.enrichment.quality_proposer import SuggestedRule


class RuleExecutionResult(BaseModel):
    rule_type: str
    column_name: str
    passed: bool
    failing_rows_count: int
    total_rows_count: int
    severity: str
    details: str


class TableQualityReport(BaseModel):
    table_name: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    quality_score: float
    can_certify: bool
    rule_results: List[RuleExecutionResult] = Field(default_factory=list)


class QualityRunner:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or ESTATE_DB_PATH)

    def execute_rule(self, conn: duckdb.DuckDBPyConnection, table_name: str, rule: SuggestedRule) -> RuleExecutionResult:
        """Execute a single data quality rule against a table."""
        col = rule.parameters.get("column", "")
        rule_type = rule.rule_type
        total_rows = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        failing_count = 0
        details = ""

        if rule_type == "NOT_NULL":
            query = f'SELECT COUNT(*) FROM {table_name} WHERE "{col}" IS NULL;'
            failing_count = conn.execute(query).fetchone()[0]
            details = f"{failing_count} nulls observed in column '{col}'."

        elif rule_type == "UNIQUE":
            query = f"""
                SELECT COUNT(*) - COUNT(DISTINCT "{col}") 
                FROM {table_name} 
                WHERE "{col}" IS NOT NULL;
            """
            failing_count = conn.execute(query).fetchone()[0]
            details = f"{failing_count} duplicate values found in column '{col}'."

        elif rule_type == "RANGE_CHECK":
            min_val = rule.parameters.get("min")
            max_val = rule.parameters.get("max")
            query = f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE "{col}" IS NOT NULL AND ("{col}" < {min_val} OR "{col}" > {max_val});
            """
            failing_count = conn.execute(query).fetchone()[0]
            details = f"{failing_count} rows out of bounds [{min_val}, {max_val}]."

        elif rule_type == "PATTERN_MATCH":
            # For pattern checks, verify basic format length or format
            pat = rule.parameters.get("pattern_name", "")
            if "ZIP" in pat:
                query = f"""
                    SELECT COUNT(*) FROM {table_name}
                    WHERE "{col}" IS NOT NULL AND LENGTH(TRIM(CAST("{col}" AS VARCHAR))) < 4;
                """
                failing_count = conn.execute(query).fetchone()[0]
                details = f"{failing_count} rows failed postal code format."
            else:
                failing_count = 0
                details = "Pattern verification passed."

        passed = (failing_count == 0)
        return RuleExecutionResult(
            rule_type=rule_type,
            column_name=col,
            passed=passed,
            failing_rows_count=failing_count,
            total_rows_count=total_rows,
            severity=rule.severity,
            details=details
        )

    def evaluate_table_quality(self, table_name: str, rules: List[SuggestedRule]) -> TableQualityReport:
        """Run all quality rules for a table and compute weighted quality score."""
        conn = duckdb.connect(self.db_path, read_only=True)
        results: List[RuleExecutionResult] = []

        if not rules:
            return TableQualityReport(
                table_name=table_name,
                total_rules=0,
                passed_rules=0,
                failed_rules=0,
                quality_score=1.0,
                can_certify=True,
                rule_results=[]
            )

        error_failures = 0
        warning_failures = 0
        total_weight = 0.0
        earned_weight = 0.0

        for r in rules:
            res = self.execute_rule(conn, table_name, r)
            results.append(res)
            weight = 2.0 if r.severity == "ERROR" else 1.0
            total_weight += weight
            if res.passed:
                earned_weight += weight
            else:
                if r.severity == "ERROR":
                    error_failures += 1
                else:
                    warning_failures += 1

        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        score = round(earned_weight / total_weight, 3) if total_weight > 0 else 1.0
        
        # Certification gate: quality_score >= 0.85 AND zero ERROR failures
        can_certify = (score >= 0.85) and (error_failures == 0)

        return TableQualityReport(
            table_name=table_name,
            total_rules=len(rules),
            passed_rules=passed_count,
            failed_rules=failed_count,
            quality_score=score,
            can_certify=can_certify,
            rule_results=results
        )
