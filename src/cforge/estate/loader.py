"""ContextForge Data Estate Loader.

Downloads real public datasets (Olist Brazilian E-commerce & Northwind)
and materializes them into raw tables and transformed models in DuckDB/PostgreSQL.
"""

from pathlib import Path
import csv
import io
import urllib.request
import duckdb
from typing import Dict, List, Optional
from cforge.config import RAW_DATA_DIR, ESTATE_DB_PATH, DATA_DIR

OLIST_BASE_URL = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
NORTHWIND_BASE_URL = "https://raw.githubusercontent.com/graphql-compose/graphql-compose-examples/master/examples/northwind/data/csv/"

OLIST_FILES = {
    "raw_olist_customers": "olist_customers_dataset.csv",
    "raw_olist_orders": "olist_orders_dataset.csv",
    "raw_olist_order_items": "olist_order_items_dataset.csv",
    "raw_olist_order_payments": "olist_order_payments_dataset.csv",
    "raw_olist_order_reviews": "olist_order_reviews_dataset.csv",
    "raw_olist_products": "olist_products_dataset.csv",
    "raw_olist_sellers": "olist_sellers_dataset.csv",
    "raw_olist_geolocation": "olist_geolocation_dataset.csv",
    "raw_olist_category_translation": "product_category_name_translation.csv",
}

NORTHWIND_FILES = {
    "raw_nw_customers": "customers.csv",
    "raw_nw_orders": "orders.csv",
    "raw_nw_order_details": "order_details.csv",
    "raw_nw_products": "products.csv",
    "raw_nw_categories": "categories.csv",
    "raw_nw_employees": "employees.csv",
    "raw_nw_shippers": "shippers.csv",
    "raw_nw_suppliers": "suppliers.csv",
}


def download_csv_sample(url: str, output_path: Path, max_rows: int = 5000) -> Path:
    """Download real public dataset CSV, retaining up to max_rows real records."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 100:
        return output_path

    req = urllib.request.Request(url, headers={"User-Agent": "ContextForge/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        lines = []
        count = 0
        reader = io.TextIOWrapper(response, encoding="utf-8", errors="replace")
        for line in reader:
            lines.append(line)
            count += 1
            if count > max_rows:
                break

    output_path.write_text("".join(lines), encoding="utf-8")
    return output_path


def load_raw_estate(max_rows_per_table: int = 5000) -> Dict[str, Path]:
    """Download and prepare all real public dataset CSV files."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    downloaded_files: Dict[str, Path] = {}

    for table_name, filename in OLIST_FILES.items():
        url = OLIST_BASE_URL + filename
        out_path = RAW_DATA_DIR / f"{table_name}.csv"
        # Geolocation has 1M rows, 5000 is plenty for real spatial profiling
        limit = 5000 if "geolocation" in filename or "reviews" in filename else 8000
        download_csv_sample(url, out_path, max_rows=limit)
        downloaded_files[table_name] = out_path

    for table_name, filename in NORTHWIND_FILES.items():
        url = NORTHWIND_BASE_URL + filename
        out_path = RAW_DATA_DIR / f"{table_name}.csv"
        download_csv_sample(url, out_path, max_rows=max_rows_per_table)
        downloaded_files[table_name] = out_path

    return downloaded_files


def init_duckdb_estate(db_path: Optional[Path] = None, force_recreate: bool = False) -> duckdb.DuckDBPyConnection:
    """Initialize DuckDB database with raw tables and execute all transformation models."""
    target_path = db_path or ESTATE_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    if force_recreate and target_path.exists():
        target_path.unlink()

    conn = duckdb.connect(str(target_path))
    raw_files = load_raw_estate()

    # Load raw tables
    for table_name, csv_path in raw_files.items():
        escaped_path = str(csv_path).replace("\\", "/")
        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{escaped_path}', header=True);
        """)

    # Run transformation models in order
    models_dir = Path(__file__).resolve().parent / "models"
    model_execution_order = [
        # Staging models
        "stg_customers.sql",
        "stg_orders.sql",
        "stg_order_items.sql",
        "stg_payments.sql",
        "stg_products.sql",
        "stg_sellers.sql",
        "stg_reviews.sql",
        # Marts & Dimensions
        "dim_customers.sql",
        "dim_products.sql",
        "dim_sellers.sql",
        "fct_orders.sql",
        "fct_order_payments.sql",
        "customer_ltv.sql",
        "mart_geo_performance.sql",
    ]

    for model_file in model_execution_order:
        sql_path = models_dir / model_file
        if sql_path.exists():
            table_name = sql_path.stem
            sql_query = sql_path.read_text(encoding="utf-8")
            conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS {sql_query}")

    return conn


def export_postgres_init_sql(output_sql_path: Optional[Path] = None) -> Path:
    """Generate init_postgres.sql for docker-compose based on DuckDB estate tables."""
    target = output_sql_path or (DATA_DIR / "init_postgres.sql")
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # We can create schema and copy statements or insert scripts for docker-compose
    conn = duckdb.connect(str(ESTATE_DB_PATH))
    tables = conn.execute("SHOW TABLES").fetchall()
    
    sql_statements = [
        "-- ContextForge Real Estate PostgreSQL Initialization Script",
        "-- Auto-generated for Docker Compose deployment",
        "CREATE SCHEMA IF NOT EXISTS raw;",
        "CREATE SCHEMA IF NOT EXISTS staging;",
        "CREATE SCHEMA IF NOT EXISTS marts;",
    ]

    # Generate tables DDL and data for PostgreSQL
    for (t_name,) in tables:
        schema_info = conn.execute(f"DESCRIBE {t_name}").fetchall()
        col_defs = []
        for col_name, col_type, null_ok, *_ in schema_info:
            pg_type = "VARCHAR"
            t_upper = col_type.upper()
            if "INT" in t_upper:
                pg_type = "BIGINT"
            elif "DOUBLE" in t_upper or "FLOAT" in t_upper or "DECIMAL" in t_upper:
                pg_type = "NUMERIC(15, 4)"
            elif "DATE" in t_upper:
                pg_type = "TIMESTAMP"
            elif "BOOL" in t_upper:
                pg_type = "BOOLEAN"
            col_defs.append(f"    {col_name} {pg_type}")
        
        create_tbl = f"CREATE TABLE IF NOT EXISTS public.{t_name} (\n" + ",\n".join(col_defs) + "\n);"
        sql_statements.append(create_tbl)

    target.write_text("\n\n".join(sql_statements), encoding="utf-8")
    return target
