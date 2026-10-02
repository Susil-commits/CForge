"""Test Suite for Step 6: Data Quality Loop and Defect Catch Rate."""

import pytest
from cforge.enrichment.quality_proposer import SuggestedRule
from cforge.quality.runner import QualityRunner, TableQualityReport
from cforge.quality.injector import DefectInjector, DefectCatchReport


def test_quality_runner_on_clean_estate():
    """Verify quality runner computes high scores and approves certification on valid tables."""
    runner = QualityRunner()
    rules = [
        SuggestedRule(rule_type="NOT_NULL", parameters={"column": "order_id"}, severity="ERROR", confidence=0.99, rationale="Primary key not null"),
        SuggestedRule(rule_type="RANGE_CHECK", parameters={"column": "payment_amount", "min": 0.0, "max": 100000.0}, severity="WARNING", confidence=0.95, rationale="Positive amount")
    ]
    report = runner.evaluate_table_quality("fct_order_payments", rules)

    assert isinstance(report, TableQualityReport)
    assert report.total_rules == 2
    assert report.passed_rules == 2
    assert report.failed_rules == 0
    assert report.quality_score >= 0.95
    assert report.can_certify


def test_certification_gate_blocks_failing_table():
    """Verify that failing ERROR quality rules strictly block asset certification."""
    runner = QualityRunner()
    # Define an impossible rule to simulate a failure
    impossible_rule = [
        SuggestedRule(rule_type="RANGE_CHECK", parameters={"column": "payment_amount", "min": 10000.0, "max": 20000.0}, severity="ERROR", confidence=0.99, rationale="Impossible bound")
    ]
    report = runner.evaluate_table_quality("fct_order_payments", impossible_rule)

    assert not report.can_certify, "Failing ERROR severity rule must block certification!"
    assert report.failed_rules == 1
    assert report.quality_score < 0.85


def test_defect_injection_benchmark_proof():
    """Verify defect injector introduces anomalies and quality rules catch them with proof statement."""
    injector = DefectInjector()
    report = injector.run_defect_benchmark()

    assert isinstance(report, DefectCatchReport)
    assert report.total_injected_defects == 5
    assert report.caught_defects >= 4, f"Expected at least 4 caught defects, got {report.caught_defects}"
    assert report.false_positives == 0
    assert report.catch_rate_percentage >= 80.0
    assert "Rules caught" in report.proof_message
    assert "injected defects" in report.proof_message
    print(f"\nStep 6 Proof Statement: '{report.proof_message}'")
