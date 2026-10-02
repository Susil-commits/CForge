"""Test Suite for Step 3: Column-Level Lineage Engine."""

from pathlib import Path
import json
import pytest
from cforge.config import PROJECT_ROOT, DATA_DIR
from cforge.lineage.parser import LineageParser
from cforge.lineage.openlineage import OpenLineageEmitter
from cforge.lineage.propagator import LineagePropagator
from cforge.lineage.eval import evaluate_lineage_accuracy


def test_sqlglot_model_parsing():
    """Verify sqlglot parses transformation models and extracts column lineage edges."""
    models_dir = PROJECT_ROOT / "src" / "cforge" / "estate" / "models"
    parser = LineageParser()
    edges = parser.parse_models_directory(models_dir)

    assert len(edges) >= 50, f"Expected >= 50 lineage edges, found {len(edges)}"

    # Check key lineage links
    targets = {f"{e.target_table}.{e.target_column}" for e in edges}
    assert "stg_customers.customer_id" in targets
    assert "stg_orders.order_id" in targets
    assert "dim_customers.customer_unique_id" in targets
    assert "dim_products.product_category" in targets
    assert "fct_orders.merchandise_total_brl" in targets
    assert "customer_ltv.customer_unique_id" in targets


def test_openlineage_event_emission():
    """Verify OpenLineage events are emitted in standard specification format."""
    models_dir = PROJECT_ROOT / "src" / "cforge" / "estate" / "models"
    parser = LineageParser()
    edges = parser.parse_models_directory(models_dir)

    # Group edges by target table
    edges_by_table = {}
    for e in edges:
        edges_by_table.setdefault(e.target_table, []).append(e)

    emitter = OpenLineageEmitter()
    out_file = DATA_DIR / "openlineage_events.json"
    p = emitter.export_all_models_to_openlineage(edges_by_table, output_file=out_file)

    assert p.exists()
    events = json.loads(p.read_text(encoding="utf-8"))
    assert len(events) >= 10

    sample_event = events[0]
    assert sample_event["eventType"] == "COMPLETE"
    assert "run" in sample_event and "runId" in sample_event["run"]
    assert "job" in sample_event and sample_event["job"]["namespace"] == "cforge.dataops"
    assert "inputs" in sample_event
    assert "outputs" in sample_event and len(sample_event["outputs"]) > 0
    assert "columnLineage" in sample_event["outputs"][0]["facets"]


def test_lineage_tag_propagation_and_reason_chain():
    """Verify PII tag propagates across multiple hops along column lineage with explainable reason chains."""
    models_dir = PROJECT_ROOT / "src" / "cforge" / "estate" / "models"
    parser = LineageParser()
    edges = parser.parse_models_directory(models_dir)

    propagator = LineagePropagator(edges)
    # Propagate from raw_olist_customers.customer_id
    propagated = propagator.propagate_tag(
        initial_table="raw_olist_customers",
        initial_column="customer_id",
        tag_name="PII",
        tag_value="CUSTOMER_ID",
        max_hops=5
    )

    assert len(propagated) > 0, "Expected downstream propagated tags"
    targets = {f"{p.target_table}.{p.target_column}" for p in propagated}
    
    # stg_customers.customer_id should be in downstream
    assert "stg_customers.customer_id" in targets

    # Inspect reason chain
    stg_cust_prop = next(p for p in propagated if p.target_column == "customer_id")
    assert len(stg_cust_prop.reason_chain) >= 2
    assert "raw_olist_customers.customer_id [PII:CUSTOMER_ID]" in stg_cust_prop.reason_chain[0]
    assert "stg_customers.customer_id" in stg_cust_prop.reason_chain[1]


def test_hand_verified_accuracy_benchmark():
    """Verify lineage accuracy against the 30 hand-verified gold columns."""
    report = evaluate_lineage_accuracy()
    assert report["total_hand_verified"] == 30
    assert report["accuracy_percentage"] >= 90.0, f"Expected >= 90% accuracy, got {report['accuracy_percentage']}%"
    assert report["correct"] >= 27
