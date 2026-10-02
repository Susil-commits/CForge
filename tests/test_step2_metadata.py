"""Test Suite for Step 2: Metadata Model, Store, and Lakehouse Export."""

from pathlib import Path
import duckdb
import pytest
from cforge.config import METADATA_DB_PATH, LAKEHOUSE_DIR
from cforge.catalog.store import MetadataStore
from cforge.catalog.lakehouse import MetadataLakehouse


@pytest.fixture(scope="module")
def populated_store(tmp_path_factory):
    test_db = tmp_path_factory.mktemp("meta") / "metadata.duckdb"
    store = MetadataStore(test_db, auto_populate=False)
    store.populate_from_estate()
    return store


def test_asset_creation_and_versioned_history(populated_store):
    """Verify that updating an asset creates a new version and appends to history log."""
    test_asset_id = "cforge.public.test_custom_table"
    populated_store.upsert_asset({
        "asset_id": test_asset_id,
        "asset_type": "TABLE",
        "name": "test_custom_table",
        "description": "Initial description",
        "certification_status": "DRAFT",
        "owner": "Data Eng"
    }, changed_by="Agent_1", reason="Initial creation")

    # Verify version 1
    asset_v1 = populated_store.conn.execute("SELECT version, description FROM assets WHERE asset_id = ?", (test_asset_id,)).fetchone()
    assert asset_v1[0] == 1
    assert asset_v1[1] == "Initial description"

    # Update asset
    populated_store.upsert_asset({
        "asset_id": test_asset_id,
        "description": "Enriched description with business context",
        "certification_status": "CERTIFIED",
        "owner": "Finance Governance"
    }, changed_by="Steward_Alice", reason="Steward approval")

    # Verify version 2
    asset_v2 = populated_store.conn.execute("SELECT version, description, certification_status FROM assets WHERE asset_id = ?", (test_asset_id,)).fetchone()
    assert asset_v2[0] == 2
    assert asset_v2[1] == "Enriched description with business context"
    assert asset_v2[2] == "CERTIFIED"

    # Verify immutable history entries
    history_rows = populated_store.conn.execute("SELECT version, change_type, changed_by, reason FROM asset_history WHERE asset_id = ? ORDER BY version", (test_asset_id,)).fetchall()
    assert len(history_rows) == 2
    assert history_rows[0][0] == 1
    assert history_rows[0][1] == "CREATE"
    assert history_rows[1][0] == 2
    assert history_rows[1][1] == "UPDATE"
    assert history_rows[1][2] == "Steward_Alice"


def test_recursive_cte_graph_traversal(populated_store):
    """Verify recursive CTE computes upstream and downstream paths correctly."""
    # Create chain A -> B -> C -> D
    nodes = ["cforge.test.chain_a", "cforge.test.chain_b", "cforge.test.chain_c", "cforge.test.chain_d"]
    for n in nodes:
        populated_store.upsert_asset({"asset_id": n, "asset_type": "TABLE", "name": n.split(".")[-1]})

    populated_store.add_lineage_edge(nodes[0], nodes[1], "ETL")
    populated_store.add_lineage_edge(nodes[1], nodes[2], "TRANSFORM")
    populated_store.add_lineage_edge(nodes[2], nodes[3], "EXPORT")

    # Downstream from A
    downstream = populated_store.get_downstream_lineage_recursive(nodes[0])
    downstream_targets = [d["target_asset_id"] for d in downstream]
    assert nodes[1] in downstream_targets
    assert nodes[2] in downstream_targets
    assert nodes[3] in downstream_targets

    # Check max depth
    max_d = max(d["depth"] for d in downstream)
    assert max_d == 3

    # Upstream from D
    upstream = populated_store.get_upstream_lineage_recursive(nodes[3])
    upstream_sources = [u["source_asset_id"] for u in upstream]
    assert nodes[2] in upstream_sources
    assert nodes[1] in upstream_sources
    assert nodes[0] in upstream_sources


def test_metadata_lakehouse_export_and_proof_query(populated_store, tmp_path):
    """Verify metadata store exports to Parquet and answers the Proof question."""
    lakehouse_dir = tmp_path / "lakehouse"
    lakehouse = MetadataLakehouse(lakehouse_dir=lakehouse_dir, metadata_db_path=populated_store.db_path)
    exported = lakehouse.export_lakehouse()

    assert "assets" in exported
    assert "tags" in exported
    assert "lineage_edges" in exported
    assert "asset_history" in exported
    for path in exported.values():
        assert path.exists()
        assert path.stat().st_size > 0

    # Execute the proof query: "which certified tables contain PII and are consumed by dashboards?"
    results = lakehouse.query_certified_tables_with_pii_consumed_by_dashboards()
    assert len(results) > 0, "Proof query returned 0 rows"
    
    table_names = {r["table_name"] for r in results}
    # certified marts like dim_customers, fct_orders, customer_ltv should appear
    assert ("dim_customers" in table_names or "fct_orders" in table_names or "customer_ltv" in table_names)

    for r in results:
        assert r["certification_status"] == "CERTIFIED"
        assert r["pii_type"] in ["CUSTOMER_ID", "POSTAL_CODE", "FINANCIAL", "CONFIDENTIAL_NOTES", "SENSITIVE"]
        assert "dashboard." in r["consumed_by_dashboard"]
