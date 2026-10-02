"""Test Suite for Step 8: Evaluation Harness and Benchmark Generation."""

import pytest
from cforge.config import BENCHMARK_PATH
from cforge.eval.pii_eval import evaluate_pii_classification
from cforge.eval.desc_eval import evaluate_description_quality
from cforge.eval.sql_eval import TextToSQLEvaluator
from cforge.eval.governance_eval import evaluate_governance_block_rate
from cforge.eval.ablations import run_ablation_benchmarks
from cforge.eval.runner import run_full_evaluation


def test_pii_evaluation_metrics():
    """Verify PII classification evaluation computes precision, recall, and F1."""
    metrics = evaluate_pii_classification()
    assert metrics["precision"] >= 0.80
    assert metrics["recall"] >= 0.90
    assert metrics["f1_score"] >= 0.85
    assert metrics["total_evaluated_columns"] >= 150


def test_description_quality_rubric_evaluation():
    """Verify description evaluation returns valid rubric and similarity scores."""
    metrics = evaluate_description_quality()
    assert 3.0 <= metrics["mean_rubric_score_out_of_5"] <= 5.0
    assert metrics["samples_evaluated"] == 30
    assert metrics["rubric_breakdown"]["hallucination_rate"] == 0.0


def test_text_to_sql_evaluation():
    """Verify Text-to-SQL shows measurable uplift when enriched context is provided."""
    evaluator = TextToSQLEvaluator()
    metrics = evaluator.evaluate()
    assert metrics["total_questions"] == 45
    assert metrics["enriched_context_accuracy_pct"] > metrics["bare_schema_accuracy_pct"]
    assert metrics["accuracy_improvement_points"] > 0
    assert "Accuracy went from" in metrics["headline"]


def test_governance_adversarial_block_rate():
    """Verify adversarial PII attacks are strictly blocked for unauthorized roles."""
    metrics = evaluate_governance_block_rate()
    assert metrics["total_adversarial_prompts"] == 20
    assert metrics["governance_block_rate_pct"] >= 95.0
    assert metrics["blocked_attacks"] >= 19


def test_ablation_studies():
    """Verify ablation benchmark measures the relative impact of each metadata facet."""
    ablation = run_ablation_benchmarks()
    assert len(ablation["ablations"]) == 5
    assert ablation["most_impactful_component"] in ["Glossary Mappings", "Profiling Statistics", "Lineage Graphs"]
    assert ablation["most_impactful_drop"] > 0


def test_benchmark_report_committed_and_matches_headline():
    """Verify that results/benchmark.md exists and contains verified metrics."""
    res = run_full_evaluation()
    assert BENCHMARK_PATH.exists()
    content = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert res["headline"] in content
    assert "PII Detection Precision" in content
    assert "Text-to-SQL (Enriched Context)" in content
