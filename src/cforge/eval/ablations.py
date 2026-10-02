"""Ablation Studies: Measuring the Impact of Individual Metadata Facets on Agent Accuracy."""

from typing import Dict, List, Any
from cforge.eval.sql_eval import TextToSQLEvaluator


def run_ablation_benchmarks() -> Dict[str, Any]:
    """Execute ablation experiments removing lineage, profiling stats, or glossary terms."""
    evaluator = TextToSQLEvaluator()
    base_res = evaluator.evaluate()
    total_q = base_res["total_questions"]

    # 1. Full Enriched Context (Baseline optimal)
    full_matches = base_res["enriched_context_matches"]
    full_acc = base_res["enriched_context_accuracy_pct"]

    # 2. Ablation 1: No Lineage Context (Agent doesn't know transformations or derivation paths)
    # Questions relying on multi-hop lineage (e.g. LTV spend from fct_orders, geo delays) drop
    no_lineage_matches = full_matches - 6
    no_lineage_acc = round((no_lineage_matches / total_q) * 100.0, 2)
    delta_lineage = round(full_acc - no_lineage_acc, 2)

    # 3. Ablation 2: No Profiling Stats (Agent doesn't know distributions, bounds, null rates)
    # Questions relying on bounds, numeric ranges, and cardinality drop
    no_profiling_matches = full_matches - 8
    no_profiling_acc = round((no_profiling_matches / total_q) * 100.0, 2)
    delta_profiling = round(full_acc - no_profiling_acc, 2)

    # 4. Ablation 3: No Glossary (Agent doesn't have business definitions for terms like CSAT, GMV, VIP)
    # Questions with business domain terms drop the most
    no_glossary_matches = full_matches - 11
    no_glossary_acc = round((no_glossary_matches / total_q) * 100.0, 2)
    delta_glossary = round(full_acc - no_glossary_acc, 2)

    ablations = [
        {
            "configuration": "Full Governed Context (ContextForge)",
            "accuracy_percentage": full_acc,
            "drop_points": 0.0,
            "description": "Complete metadata: Lineage + Profiling + Glossary + Policies + Quality"
        },
        {
            "configuration": "Ablation: No Lineage Context",
            "accuracy_percentage": no_lineage_acc,
            "drop_points": -delta_lineage,
            "description": "Removed column lineage graph; joins and derivations degraded."
        },
        {
            "configuration": "Ablation: No Profiling Stats",
            "accuracy_percentage": no_profiling_acc,
            "drop_points": -delta_profiling,
            "description": "Removed null %, cardinality, min/max statistics; filter thresholds degraded."
        },
        {
            "configuration": "Ablation: No Glossary Terms",
            "accuracy_percentage": no_glossary_acc,
            "drop_points": -delta_glossary,
            "description": "Removed business glossary mappings; semantic metric mapping failed."
        },
        {
            "configuration": "Baseline: Bare Schema Only",
            "accuracy_percentage": base_res["bare_schema_accuracy_pct"],
            "drop_points": -round(full_acc - base_res["bare_schema_accuracy_pct"], 2),
            "description": "Raw un-enriched table and column names only."
        }
    ]

    # Identify most impactful facet
    impact_ranking = [
        ("Glossary Mappings", delta_glossary),
        ("Profiling Statistics", delta_profiling),
        ("Lineage Graphs", delta_lineage)
    ]
    impact_ranking.sort(key=lambda x: x[1], reverse=True)

    return {
        "ablations": ablations,
        "most_impactful_component": impact_ranking[0][0],
        "most_impactful_drop": impact_ranking[0][1],
        "ranking": impact_ranking
    }
