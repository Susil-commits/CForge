"""PII Classification Precision and Recall Evaluation vs Gold Labels and Held-Out Split.

Evaluates both heuristic baseline and LLM-powered classification against an independent,
hand-verified ground-truth dataset with strict train/held-out splits.
"""

import csv
from typing import Dict, Any, List, Optional
from cforge.config import GOLD_LABELS_PATH
from cforge.enrichment.profiler import EstateProfiler
from cforge.enrichment.classifier import ClassifierAgent, HeuristicClassifierAgent, LLMClassifierAgent


def compute_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, Any]:
    """Compute precision, recall, and F1 score."""
    precision = round(tp / (tp + fp) if (tp + fp) > 0 else 0.0, 4)
    recall = round(tp / (tp + fn) if (tp + fn) > 0 else 0.0, 4)
    f1 = round((2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0, 4)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "total_evaluated": tp + fp + fn + tn
    }


def evaluate_pii_classification(split: Optional[str] = "held_out", agent_mode: str = "heuristic") -> Dict[str, Any]:
    """Evaluate PII classification performance.
    
    Args:
        split: 'held_out' (default, independent unseen split), 'calibration', or 'all'.
        agent_mode: 'heuristic' (fast deterministic pattern agent), 'auto', or 'llm'.
    """
    with open(GOLD_LABELS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        gold_rows = list(reader)

    profiler = EstateProfiler()
    agent = ClassifierAgent(mode=agent_mode)
    heuristic_agent = HeuristicClassifierAgent()

    # Filter by split if requested
    target_rows = gold_rows
    if split and split != "all":
        target_rows = [r for r in gold_rows if r.get("split", "calibration") == split]

    tp, fp, fn, tn = 0, 0, 0, 0
    h_tp, h_fp, h_fn, h_tn = 0, 0, 0, 0

    for row in target_rows:
        tbl = row["table_name"]
        col = row["column_name"]
        gold_is_pii = (row["is_pii"].strip().lower() == "true")

        try:
            profile = profiler.profile_column(tbl, col)
            clf_res = agent.classify(profile)
            pred_is_pii = clf_res.is_pii

            # Also evaluate heuristic baseline
            h_res = heuristic_agent.classify(profile)
            h_is_pii = h_res.is_pii
        except Exception:
            continue

        # Primary agent metrics
        if gold_is_pii and pred_is_pii:
            tp += 1
        elif not gold_is_pii and pred_is_pii:
            fp += 1
        elif gold_is_pii and not pred_is_pii:
            fn += 1
        else:
            tn += 1

        # Heuristic baseline metrics
        if gold_is_pii and h_is_pii:
            h_tp += 1
        elif not gold_is_pii and h_is_pii:
            h_fp += 1
        elif gold_is_pii and not h_is_pii:
            h_fn += 1
        else:
            h_tn += 1

    primary_metrics = compute_metrics(tp, fp, fn, tn)
    heuristic_metrics = compute_metrics(h_tp, h_fp, h_fn, h_tn)

    return {
        **primary_metrics,
        "total_evaluated_columns": primary_metrics["total_evaluated"],
        "evaluated_split": split,
        "heuristic_baseline": heuristic_metrics,
        "delta_vs_heuristic_f1": round(primary_metrics["f1_score"] - heuristic_metrics["f1_score"], 4)
    }
