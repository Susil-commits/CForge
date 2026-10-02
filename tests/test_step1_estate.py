"""Test Suite for Step 1: Real Data Estate."""

from pathlib import Path
import csv
import duckdb
import pytest
from cforge.config import ESTATE_DB_PATH, GOLD_LABELS_PATH, DATA_DIR
from cforge.estate.loader import init_duckdb_estate, export_postgres_init_sql


def test_gold_labels_exists_and_meets_quota():
    """Verify data/gold_labels.csv is present and contains >= 150 columns."""
    assert GOLD_LABELS_PATH.exists(), f"Missing {GOLD_LABELS_PATH}"
    
    with open(GOLD_LABELS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 150, f"Expected >= 150 columns, found {len(rows)}"
    
    required_fields = {
        "table_name",
        "column_name",
        "data_type",
        "is_pii",
        "pii_type",
        "true_business_description",
        "glossary_term"
    }
    assert set(reader.fieldnames or []).issuperset(required_fields)
    
    # Ensure some columns are PII and some are not
    pii_count = sum(1 for r in rows if r["is_pii"].lower() == "true")
    non_pii_count = sum(1 for r in rows if r["is_pii"].lower() == "false")
    assert pii_count > 10
    assert non_pii_count > 50


def test_duckdb_estate_materialization():
    """Verify DuckDB estate loads raw public datasets and builds transformation models."""
    conn = init_duckdb_estate()
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    
    # Check essential raw tables exist
    expected_raw = [
        "raw_olist_customers",
        "raw_olist_orders",
        "raw_olist_order_items",
        "raw_olist_products",
        "raw_nw_customers",
        "raw_nw_orders",
        "raw_nw_products"
    ]
    for raw_tbl in expected_raw:
        assert raw_tbl in tables, f"Expected {raw_tbl} in estate"
        count = conn.execute(f"SELECT COUNT(*) FROM {raw_tbl}").fetchone()[0]
        assert count > 0, f"Table {raw_tbl} is unexpectedly empty"

    # Check essential staging and mart models exist and have data
    expected_models = [
        "stg_customers",
        "stg_orders",
        "stg_order_items",
        "stg_products",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "fct_orders",
        "fct_order_payments",
        "customer_ltv",
        "mart_geo_performance"
    ]
    for model in expected_models:
        assert model in tables, f"Expected {model} in estate"
        count = conn.execute(f"SELECT COUNT(*) FROM {model}").fetchone()[0]
        assert count > 0, f"Model {model} is unexpectedly empty"


def test_postgres_init_export():
    """Verify init_postgres.sql is exported and contains table definitions."""
    sql_file = export_postgres_init_sql()
    assert sql_file.exists()
    content = sql_file.read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS marts;" in content
    assert "CREATE TABLE IF NOT EXISTS public.fct_orders" in content
    assert "CREATE TABLE IF NOT EXISTS public.customer_ltv" in content
