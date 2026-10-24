"""Test Suite for Step 8: Evaluation Harness and Benchmark Generation."""

from cforge.config import BENCHMARK_PATH
from cforge.eval.ablations import run_ablation_benchmarks
from cforge.eval.desc_eval import evaluate_description_quality
from cforge.eval.governance_eval import evaluate_governance_block_rate
from cforge.eval.pii_eval import evaluate_pii_classification
from cforge.eval.runner import run_full_evaluation
from cforge.eval.sql_eval import TextToSQLEvaluator


def test_pii_evaluation_metrics():
    """Verify PII classification evaluation computes precision, recall, and F1 on held-out and full sets."""
    held_out = evaluate_pii_classification(split="held_out")
    assert held_out["precision"] >= 0.80
    assert held_out["recall"] >= 0.85
    assert held_out["f1_score"] >= 0.85
    assert held_out["total_evaluated_columns"] >= 40

    full = evaluate_pii_classification(split="all")
    assert full["total_evaluated_columns"] >= 150
    assert full["f1_score"] >= 0.85


def test_description_quality_rubric_evaluation():
    """Verify description evaluation returns valid rubric and quality scores."""
    metrics = evaluate_description_quality()
    assert 3.0 <= metrics["mean_rubric_score_out_of_5"] <= 5.0
    assert metrics["samples_evaluated"] >= 25
    assert metrics["rubric_breakdown"]["hallucination_rate"] <= 0.20
    assert metrics["rubric_breakdown"]["technical_grounding"] >= 3.5


def test_text_to_sql_evaluation():
    """Verify Text-to-SQL shows measurable uplift when enriched context is provided."""
    evaluator = TextToSQLEvaluator()
    metrics = evaluator.evaluate()
    assert metrics["total_questions"] == 45
    assert metrics["enriched_context_accuracy_pct"] > metrics["bare_schema_accuracy_pct"]
    assert metrics["accuracy_improvement_points"] > 0
    assert "Accuracy went from" in metrics["headline"]


def test_governance_adversarial_block_rate_and_false_refusals():
    """Verify adversarial PII attacks and benign queries are evaluated with documented boundary cases."""
    metrics = evaluate_governance_block_rate()
    assert metrics["total_adversarial_prompts"] >= 20
    assert metrics["governance_block_rate_pct"] >= 80.0
    assert metrics["total_benign_prompts"] >= 20
    assert metrics["benign_pass_rate_pct"] >= 80.0
    assert len(metrics["leaked_samples"]) >= 1
    assert len(metrics["false_refusal_samples"]) >= 1


def test_ablation_studies():
    """Verify ablation benchmark measures overall gain and acknowledges noise at n=45."""
    ablation = run_ablation_benchmarks()
    assert len(ablation["ablations"]) == 5
    assert "Only the overall gain is clear" in ablation["key_finding"]


def test_benchmark_report_committed_and_matches_headline():
    """Verify that results/benchmark.md exists and contains verified metrics."""
    res = run_full_evaluation()
    assert BENCHMARK_PATH.exists()
    content = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert res["headline"] in content
    assert "PII Detection Precision" in content
    assert "Text-to-SQL (Enriched Context)" in content
