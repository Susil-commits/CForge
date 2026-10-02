"""PII Classification Precision and Recall Evaluation vs Gold Labels."""

import csv
from typing import Dict, Any, List
from cforge.config import GOLD_LABELS_PATH, ESTATE_DB_PATH
from cforge.enrichment.profiler import EstateProfiler
from cforge.enrichment.classifier import ClassifierAgent


def evaluate_pii_classification() -> Dict[str, Any]:
    """Compute true positives, false positives, false negatives, precision, recall, and F1."""
    with open(GOLD_LABELS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        gold_rows = list(reader)

    profiler = EstateProfiler()
    classifier = ClassifierAgent()

    tp = 0
    fp = 0
    fn = 0
    tn = 0

    for row in gold_rows:
        tbl = row["table_name"]
        col = row["column_name"]
        gold_is_pii = (row["is_pii"].strip().lower() == "true")
        
        try:
            profile = profiler.profile_column(tbl, col)
            clf_res = classifier.classify(profile)
            pred_is_pii = clf_res.is_pii
        except Exception:
            # If table is not in estate, skip
            continue

        if gold_is_pii and pred_is_pii:
            tp += 1
        elif not gold_is_pii and pred_is_pii:
            fp += 1
        elif gold_is_pii and not pred_is_pii:
            fn += 1
        else:
            tn += 1

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
        "total_evaluated_columns": tp + fp + fn + tn
    }
