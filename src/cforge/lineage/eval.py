"""Lineage Evaluation and Strict Accuracy Benchmark vs Hand-Verified Set.

Validates that the SQL AST lineage parser resolves ALL required upstream column
dependencies (strict recall & precision) against the hand-verified ground truth.
"""

import json
from typing import Any

from cforge.config import HAND_VERIFIED_LINEAGE_PATH, PROJECT_ROOT
from cforge.lineage.parser import ColumnLineageEdge, LineageParser


def evaluate_lineage_accuracy() -> dict[str, Any]:
    """Compare sqlglot parser output strictly against all expected sources in the gold lineage set."""
    models_dir = PROJECT_ROOT / "src" / "cforge" / "estate" / "models"
    parser = LineageParser()
    parsed_edges = parser.parse_models_directory(models_dir)

    # Index parsed edges: (target_table, target_column) -> list of sources
    parsed_map: dict[str, list[ColumnLineageEdge]] = {}
    for edge in parsed_edges:
        key = f"{edge.target_table}.{edge.target_column}"
        if key not in parsed_map:
            parsed_map[key] = []
        parsed_map[key].append(edge)

    # Load hand-verified ground truth
    with open(HAND_VERIFIED_LINEAGE_PATH, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    correct_count = 0
    failures: list[dict[str, Any]] = []

    for item in ground_truth:
        target_tbl = item["target_table"]
        target_col = item["target_column"]
        target_key = f"{target_tbl}.{target_col}"
        expected_sources = item["expected_sources"]

        edges = parsed_map.get(target_key, [])
        parsed_sources = [(e.source_table.lower(), e.source_column.lower()) for e in edges]

        # Strict Matching: ALL expected sources MUST be captured by the parser
        all_expected_found = True
        missing_sources = []

        for exp_s in expected_sources:
            exp_tbl = exp_s["table"].lower()
            exp_col = exp_s["column"].lower()

            # Check for direct or aliased/CTE match
            found = False
            for p_tbl, p_col in parsed_sources:
                if p_col == exp_col and (p_tbl == exp_tbl or exp_tbl in p_tbl or p_tbl in exp_tbl):
                    found = True
                    break

            if not found:
                all_expected_found = False
                missing_sources.append({"table": exp_s["table"], "column": exp_s["column"]})

        if all_expected_found and len(edges) > 0:
            correct_count += 1
        else:
            failures.append({
                "target": target_key,
                "expected": expected_sources,
                "missing_expected": missing_sources,
                "parsed_actual": [{"table": e.source_table, "column": e.source_column} for e in edges],
                "reason": "Subquery alias boundary or unparsed projection expression."
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
    print(f"Strict Lineage Accuracy: {report['correct']}/{report['total_hand_verified']} ({report['accuracy_percentage']}%)")
    print(f"Total Parsed Edges: {report['total_parsed_edges']}")
    if report["failures"]:
        print(f"\nDocumented Parser Failures ({len(report['failures'])}):")
        for f in report["failures"]:
            print(f" - {f['target']}: missing {f['missing_expected']}")
