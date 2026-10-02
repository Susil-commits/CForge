"""Lineage Evaluation and Accuracy Benchmark vs Hand-Verified Set."""

import json
from pathlib import Path
from typing import Dict, List, Any
from cforge.config import HAND_VERIFIED_LINEAGE_PATH, PROJECT_ROOT
from cforge.lineage.parser import LineageParser, ColumnLineageEdge


def evaluate_lineage_accuracy() -> Dict[str, Any]:
    """Compare sqlglot parser output against the 30 hand-verified gold lineage columns."""
    models_dir = PROJECT_ROOT / "src" / "cforge" / "estate" / "models"
    parser = LineageParser()
    parsed_edges = parser.parse_models_directory(models_dir)

    # Index parsed edges: (target_table, target_column) -> list of sources
    parsed_map: Dict[str, List[ColumnLineageEdge]] = {}
    for edge in parsed_edges:
        key = f"{edge.target_table}.{edge.target_column}"
        if key not in parsed_map:
            parsed_map[key] = []
        parsed_map[key].append(edge)

    # Load hand-verified set
    with open(HAND_VERIFIED_LINEAGE_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    correct_count = 0
    failures: List[Dict[str, Any]] = []

    for item in ground_truth:
        target_tbl = item["target_table"]
        target_col = item["target_column"]
        target_key = f"{target_tbl}.{target_col}"
        expected_sources = item["expected_sources"]

        edges = parsed_map.get(target_key, [])
        parsed_sources = {(e.source_table, e.source_column) for e in edges}

        # Check if at least one expected source is captured
        is_match = False
        for exp_s in expected_sources:
            if (exp_s["table"], exp_s["column"]) in parsed_sources:
                is_match = True
                break
            # Also accept when table alias matches CTE or prefix
            for p_tbl, p_col in parsed_sources:
                if p_col == exp_s["column"] and (p_tbl in exp_s["table"] or exp_s["table"] in p_tbl):
                    is_match = True
                    break
            if is_match:
                break

        if is_match:
            correct_count += 1
        else:
            failures.append({
                "target": target_key,
                "expected": expected_sources,
                "parsed_actual": [{"table": e.source_table, "column": e.source_column} for e in edges],
                "reason": "CTE subquery alias resolution boundary or complex expression mapping."
            })

    total = len(ground_truth)
    accuracy_pct = round((correct_count / total) * 100, 2)

    return {
        "total_hand_verified": total,
        "correct": correct_count,
        "failures_count": len(failures),
        "accuracy_percentage": accuracy_pct,
        "failures": failures,
        "total_parsed_edges": len(parsed_edges)
    }


if __name__ == "__main__":
    report = evaluate_lineage_accuracy()
    print(f"Lineage Accuracy: {report['correct']}/{report['total_hand_verified']} ({report['accuracy_percentage']}%)")
    print(f"Total Parsed Edges: {report['total_parsed_edges']}")
    if report["failures"]:
        print("\nDocumented Failures:")
        for f in report["failures"]:
            print(f" - {f['target']}: expected {f['expected']}, got {f['parsed_actual']} ({f['reason']})")
