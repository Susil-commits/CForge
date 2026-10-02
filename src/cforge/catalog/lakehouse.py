"""Metadata Lakehouse Exporter and Query Engine.

Exports ContextForge metadata catalog to Parquet tables and enables
analytical SQL querying over metadata (lakehouse architecture).
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import duckdb
from cforge.config import LAKEHOUSE_DIR, METADATA_DB_PATH
from cforge.catalog.store import MetadataStore


class MetadataLakehouse:
    def __init__(self, lakehouse_dir: Optional[Path] = None, metadata_db_path: Optional[Path] = None):
        self.lakehouse_dir = lakehouse_dir or LAKEHOUSE_DIR
        self.lakehouse_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_db_path = metadata_db_path or METADATA_DB_PATH

    def export_lakehouse(self) -> Dict[str, Path]:
        """Export all catalog tables to individual Parquet files."""
        store = MetadataStore(self.metadata_db_path)
        tables = ["assets", "tags", "glossary_terms", "asset_glossary_mappings", "lineage_edges", "asset_history"]
        exported: Dict[str, Path] = {}

        for table in tables:
            parquet_path = self.lakehouse_dir / f"{table}.parquet"
            escaped_path = str(parquet_path).replace("\\", "/")
            store.conn.execute(f"COPY {table} TO '{escaped_path}' (FORMAT 'PARQUET');")
            exported[table] = parquet_path

        return exported

    def query(self, sql_query: str) -> List[tuple]:
        """Execute analytical SQL query directly against the Parquet metadata lakehouse."""
        conn = duckdb.connect()
        # Register views pointing directly to the Parquet files
        for tbl in ["assets", "tags", "glossary_terms", "asset_glossary_mappings", "lineage_edges", "asset_history"]:
            p_file = self.lakehouse_dir / f"{tbl}.parquet"
            if p_file.exists():
                escaped = str(p_file).replace("\\", "/")
                conn.execute(f"CREATE OR REPLACE VIEW {tbl} AS SELECT * FROM read_parquet('{escaped}');")
        
        return conn.execute(sql_query).fetchall()

    def query_certified_tables_with_pii_consumed_by_dashboards(self) -> List[Dict[str, Any]]:
        """Answers: 'Which certified tables contain PII and are consumed by dashboards?'

        Straight from the Parquet lakehouse export using DuckDB!
        """
        sql = """
            WITH RECURSIVE dashboard_lineage AS (
                -- Direct edges into dashboards
                SELECT
                    source_asset_id,
                    target_asset_id,
                    CAST(target_asset_id AS VARCHAR) AS downstream_path
                FROM lineage_edges
                WHERE target_asset_id LIKE '%.dashboard.%' 
                   OR target_asset_id LIKE 'dashboard.%'
                   OR target_asset_id LIKE '%dashboard%'

                UNION ALL

                -- Traverse backwards up to tables/columns
                SELECT
                    e.source_asset_id,
                    e.target_asset_id,
                    CAST(e.target_asset_id || ' -> ' || dl.downstream_path AS VARCHAR) AS downstream_path
                FROM lineage_edges e
                JOIN dashboard_lineage dl ON e.target_asset_id = dl.source_asset_id
            ),
            pii_columns AS (
                -- Columns tagged as PII
                SELECT DISTINCT
                    a.asset_id AS column_asset_id,
                    a.parent_id AS table_asset_id,
                    a.name AS column_name,
                    t.tag_name,
                    t.tag_value AS pii_type,
                    t.confidence
                FROM assets a
                JOIN tags t ON a.asset_id = t.asset_id
                WHERE (t.tag_name = 'PII' OR t.tag_name LIKE 'PII%')
            ),
            certified_tables AS (
                SELECT
                    asset_id AS table_asset_id,
                    name AS table_name,
                    owner,
                    certification_status,
                    quality_score
                FROM assets
                WHERE asset_type = 'TABLE'
                  AND certification_status = 'CERTIFIED'
            )
            SELECT DISTINCT
                ct.table_name,
                ct.certification_status,
                ct.owner,
                pc.column_name,
                pc.pii_type,
                dl.downstream_path AS consumed_by_dashboard
            FROM certified_tables ct
            JOIN pii_columns pc ON ct.table_asset_id = pc.table_asset_id
            JOIN dashboard_lineage dl ON (ct.table_asset_id = dl.source_asset_id OR pc.column_asset_id = dl.source_asset_id)
            ORDER BY ct.table_name, pc.column_name;
        """
        results = self.query(sql)
        output = []
        for r in results:
            output.append({
                "table_name": r[0],
                "certification_status": r[1],
                "owner": r[2],
                "column_name": r[3],
                "pii_type": r[4],
                "consumed_by_dashboard": r[5]
            })
        return output
