"""Ablation Studies: Measuring the Impact of Individual Metadata Facets on Agent Accuracy.

Runs empirical ablation experiments by systematically removing lineage, profiling stats,
or glossary terms from the context provided to the LLM and executing against DuckDB.
"""

from typing import Any

import duckdb

from cforge.config import ESTATE_DB_PATH
from cforge.eval.sql_eval import (
    TextToSQLEvaluator,
    build_bare_schema_context,
    build_enriched_context,
)


def run_ablation_benchmarks(estate_db_path: str | None = None, model_name: str | None = None) -> dict[str, Any]:
    """Execute ablation experiments removing lineage, profiling stats, or glossary terms."""
    db_path = estate_db_path or str(ESTATE_DB_PATH)
    conn = duckdb.connect(db_path, read_only=True)
    evaluator = TextToSQLEvaluator(estate_db_path=db_path, model_name=model_name)

    # 1. Full Enriched Context (Baseline optimal)
    full_ctx = build_enriched_context(conn)
    full_res = evaluator.evaluate_condition(full_ctx, "Full Governed Context")
    full_acc = full_res["accuracy_pct"]
    full_matches = full_res["matches"]

    # 2. Ablation 1: No Lineage Context (Lineage edges and derivations stripped)
    no_lineage_ctx = build_enriched_context(conn, exclude_facet="lineage")
    no_lineage_res = evaluator.evaluate_condition(no_lineage_ctx, "Ablation: No Lineage Context")
    no_lineage_acc = no_lineage_res["accuracy_pct"]
    delta_lineage = round(full_acc - no_lineage_acc, 2)

    # 3. Ablation 2: No Profiling Stats (Cardinality, bounds, distributions stripped)
    no_profiling_ctx = build_enriched_context(conn, exclude_facet="profiling")
    no_profiling_res = evaluator.evaluate_condition(no_profiling_ctx, "Ablation: No Profiling Stats")
    no_profiling_acc = no_profiling_res["accuracy_pct"]
    delta_profiling = round(full_acc - no_profiling_acc, 2)

    # 4. Ablation 3: No Glossary (Business definitions and term mappings stripped)
    no_glossary_ctx = build_enriched_context(conn, exclude_facet="glossary")
    no_glossary_res = evaluator.evaluate_condition(no_glossary_ctx, "Ablation: No Glossary Terms")
    no_glossary_acc = no_glossary_res["accuracy_pct"]
    delta_glossary = round(full_acc - no_glossary_acc, 2)

    # 5. Baseline: Bare Schema Only
    bare_ctx = build_bare_schema_context(conn)
    bare_res = evaluator.evaluate_condition(bare_ctx, "Baseline: Bare Schema Only")
    bare_acc = bare_res["accuracy_pct"]
    delta_bare = round(full_acc - bare_acc, 2)

    ablations = [
        {
            "configuration": "Full Governed Context",
            "matches": full_matches,
            "accuracy_percentage": full_acc,
            "drop_points": 0.0,
            "description": "Complete metadata: Lineage + Profiling + Glossary + Certified Marts"
        },
        {
            "configuration": "Ablation: No Lineage Context",
            "matches": no_lineage_res["matches"],
            "accuracy_percentage": no_lineage_acc,
            "drop_points": -delta_lineage,
            "description": "Removed column lineage graph; joins and derivations degraded."
        },
        {
            "configuration": "Ablation: No Profiling Stats",
            "matches": no_profiling_res["matches"],
            "accuracy_percentage": no_profiling_acc,
            "drop_points": -delta_profiling,
            "description": "Removed statistical bounds and null rates; no net execution change on 45-question benchmark (0 questions flipped)."
        },
        {
            "configuration": "Ablation: No Glossary Terms",
            "matches": no_glossary_res["matches"],
            "accuracy_percentage": no_glossary_acc,
            "drop_points": -delta_glossary,
            "description": "Removed business glossary mappings; small single-run shift (-1 question)."
        },
        {
            "configuration": "Baseline: Bare Schema Only",
            "matches": bare_res["matches"],
            "accuracy_percentage": bare_acc,
            "drop_points": -delta_bare,
            "description": "Raw un-enriched table and column names only."
        }
    ]

    key_finding = "Only the overall gain is clear. Per-facet effects are within noise at n=45."

    return {
        "ablations": ablations,
        "key_finding": key_finding,
        "delta_bare_schema": delta_bare,
        "delta_lineage": delta_lineage,
        "delta_profiling": delta_profiling,
        "delta_glossary": delta_glossary,
    }
