"""Test Suite for Step 10: Portability and Packaging Adapters."""

import pytest
from cforge.catalog.models import Asset, Tag, GlossaryTerm, LineageEdge, AssetType, CertificationStatus
from cforge.adapters.file_adapter import FileJsonAdapter
from cforge.adapters.duckdb_adapter import DuckDBCatalogAdapter


@pytest.fixture
def sample_asset():
    return Asset(
        asset_id="cforge.test.adapter_table",
        asset_type=AssetType.TABLE,
        name="adapter_table",
        display_name="Adapter Test Table",
        description="Testing catalog adapter portability",
        certification_status=CertificationStatus.CERTIFIED,
        owner="Architecture Guild"
    )


@pytest.fixture
def sample_tag():
    return Tag(
        tag_id="tag_adapter_1",
        asset_id="cforge.test.adapter_table.col1",
        tag_name="PII",
        tag_value="CUSTOMER_ID",
        confidence=0.98,
        source="AGENT"
    )


@pytest.fixture
def sample_glossary():
    return GlossaryTerm(
        term_id="glossary.adapter_term",
        term_name="Adapter Term",
        definition="Standardized term definition for adapter testing.",
        domain="Core Architecture"
    )


@pytest.fixture
def sample_edge():
    return LineageEdge(
        edge_id="edge_adapter_1",
        source_asset_id="cforge.test.table_a",
        target_asset_id="cforge.test.table_b",
        transformation_type="ETL_SYNC"
    )


def test_file_json_adapter_roundtrip(tmp_path, sample_asset, sample_tag, sample_glossary, sample_edge):
    """Verify FileJsonAdapter pushes and pulls assets, tags, glossary, and lineage with complete fidelity."""
    json_path = tmp_path / "test_bundle.json"
    adapter = FileJsonAdapter(json_path)

    # Push
    assert adapter.push_assets([sample_asset])
    assert adapter.push_tags([sample_tag])
    assert adapter.push_glossary([sample_glossary])
    assert adapter.push_lineage([sample_edge])

    # Pull
    pulled_assets = adapter.pull_assets()
    assert len(pulled_assets) == 1
    assert pulled_assets[0].asset_id == sample_asset.asset_id
    assert pulled_assets[0].display_name == sample_asset.display_name

    pulled_tags = adapter.pull_tags()
    assert len(pulled_tags) == 1
    assert pulled_tags[0].tag_name == "PII"

    pulled_gloss = adapter.pull_glossary()
    assert len(pulled_gloss) == 1
    assert pulled_gloss[0].term_name == "Adapter Term"

    pulled_edges = adapter.pull_lineage()
    assert len(pulled_edges) == 1
    assert pulled_edges[0].source_asset_id == sample_edge.source_asset_id


def test_duckdb_adapter_sync(tmp_path, sample_asset, sample_tag, sample_glossary, sample_edge):
    """Verify DuckDBCatalogAdapter syncs with live DuckDB metadata store."""
    db_file = tmp_path / "adapter_test.duckdb"
    adapter = DuckDBCatalogAdapter(db_file)

    # Push
    assert adapter.push_assets([sample_asset])
    assert adapter.push_tags([sample_tag])
    assert adapter.push_glossary([sample_glossary])
    assert adapter.push_lineage([sample_edge])

    # Pull
    assets = adapter.pull_assets()
    asset_ids = [a.asset_id for a in assets]
    assert sample_asset.asset_id in asset_ids

    tags = adapter.pull_tags()
    tag_names = [t.tag_name for t in tags]
    assert "PII" in tag_names

    glossary = adapter.pull_glossary()
    term_names = [g.term_name for g in glossary]
    assert "Adapter Term" in term_names

    edges = adapter.pull_lineage()
    assert any(e.source_asset_id == sample_edge.source_asset_id for e in edges)
