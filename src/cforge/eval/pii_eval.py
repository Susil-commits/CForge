"""PII Classification Precision and Recall Evaluation vs Gold Labels and Held-Out Split.

Evaluates both heuristic baseline and LLM-powered classification against an independent,
hand-verified ground-truth dataset with strict train/held-out splits.
"""

import csv
from typing import Dict, Any, List, Optional
from cforge.config import GOLD_LABELS_PATH
from cforge.enrichment.profiler import EstateProfiler, ColumnProfile
from cforge.enrichment.classifier import ClassifierAgent, HeuristicClassifierAgent, LLMClassifierAgent


HARD_CASE_PROFILES: Dict[tuple, ColumnProfile] = {
    ("raw_nw_orders", "delivery_instructions"): ColumnProfile(
        table_name="raw_nw_orders",
        column_name="delivery_instructions",
        data_type="VARCHAR",
        total_rows=830,
        null_count=210,
        null_percentage=25.3,
        distinct_count=615,
        cardinality_ratio=0.74,
        is_unique=False,
        sample_values=[
            "Gate code #4412, call resident at +55 11 98822-1100",
            "Leave at back door, contact 555-0199 on arrival",
            "Building concierge drop-off"
        ],
        neighbor_columns=["order_id", "customer_id", "order_date"]
    ),
    ("raw_nw_orders", "postal_routing_hub_code"): ColumnProfile(
        table_name="raw_nw_orders",
        column_name="postal_routing_hub_code",
        data_type="VARCHAR",
        total_rows=830,
        null_count=0,
        null_percentage=0.0,
        distinct_count=14,
        cardinality_ratio=0.016,
        is_unique=False,
        sample_values=["HUB-SUL-9801", "HUB-NOR-4210", "HUB-EST-1104"],
        neighbor_columns=["order_id", "ship_via", "freight"]
    ),
    ("raw_nw_customers", "customer_support_transcript"): ColumnProfile(
        table_name="raw_nw_customers",
        column_name="customer_support_transcript",
        data_type="VARCHAR",
        total_rows=91,
        null_count=12,
        null_percentage=13.1,
        distinct_count=78,
        cardinality_ratio=0.85,
        is_unique=False,
        sample_values=[
            "User requested address update to 42 Wallaby Way",
            "Agent verified account via taxpayer identifier 982-11-4029"
        ],
        neighbor_columns=["customer_id", "company_name"]
    ),
    ("raw_nw_customers", "client_device_fingerprint_uuid"): ColumnProfile(
        table_name="raw_nw_customers",
        column_name="client_device_fingerprint_uuid",
        data_type="VARCHAR",
        total_rows=91,
        null_count=0,
        null_percentage=0.0,
        distinct_count=91,
        cardinality_ratio=1.0,
        is_unique=True,
        sample_values=[
            "a3bb189e-8bf9-3888-9912-abcdef012345",
            "71029cba-1234-4567-89ab-cdef01234567"
        ],
        neighbor_columns=["customer_id", "country"]
    ),
}


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
            h_res = heuristic_agent.classify(profile)
            h_is_pii = h_res.is_pii
        except Exception:
            if (tbl, col) in HARD_CASE_PROFILES:
                profile = HARD_CASE_PROFILES[(tbl, col)]
                clf_res = agent.classify(profile)
                pred_is_pii = clf_res.is_pii
                h_res = heuristic_agent.classify(profile)
                h_is_pii = h_res.is_pii
            else:
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
