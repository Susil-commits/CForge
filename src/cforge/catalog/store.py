"""Metadata Store and Graph Traversal Engine.

Stores and queries assets, tags, glossary, lineage edges, and versioned history.
Implements recursive CTEs for graph traversal and downstream impact analysis.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import uuid
import duckdb
from cforge.config import METADATA_DB_PATH, ESTATE_DB_PATH, GOLD_LABELS_PATH
from cforge.catalog.models import AssetType, CertificationStatus, TagSource


class MetadataStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or METADATA_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self):
        """Create metadata relational tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id VARCHAR PRIMARY KEY,
                parent_id VARCHAR,
                asset_type VARCHAR,
                name VARCHAR,
                display_name VARCHAR,
                description VARCHAR,
                data_type VARCHAR,
                owner VARCHAR,
                certification_status VARCHAR,
                quality_score DOUBLE,
                version INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tags (
                tag_id VARCHAR PRIMARY KEY,
                asset_id VARCHAR,
                tag_name VARCHAR,
                tag_value VARCHAR,
                confidence DOUBLE,
                source VARCHAR,
                reason VARCHAR,
                created_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS glossary_terms (
                term_id VARCHAR PRIMARY KEY,
                term_name VARCHAR,
                definition VARCHAR,
                domain VARCHAR
            );

            CREATE TABLE IF NOT EXISTS asset_glossary_mappings (
                mapping_id VARCHAR PRIMARY KEY,
                asset_id VARCHAR,
                term_id VARCHAR,
                confidence DOUBLE,
                mapped_by VARCHAR
            );

            CREATE TABLE IF NOT EXISTS lineage_edges (
                edge_id VARCHAR PRIMARY KEY,
                source_asset_id VARCHAR,
                target_asset_id VARCHAR,
                transformation_type VARCHAR,
                transformation_logic VARCHAR,
                created_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS asset_history (
                history_id VARCHAR PRIMARY KEY,
                asset_id VARCHAR,
                version INTEGER,
                change_type VARCHAR,
                changed_by VARCHAR,
                before_state VARCHAR,
                after_state VARCHAR,
                reason VARCHAR,
                timestamp TIMESTAMP
            );
        """)

    def record_history(self, asset_id: str, version: int, change_type: str, changed_by: str,
                       before_state: Optional[Dict[str, Any]], after_state: Dict[str, Any],
                       reason: Optional[str] = None):
        """Record an immutable versioned entry in the asset history log."""
        history_id = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO asset_history 
            (history_id, asset_id, version, change_type, changed_by, before_state, after_state, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, current_timestamp)
        """, (
            history_id,
            asset_id,
            version,
            change_type,
            changed_by,
            json.dumps(before_state, default=str) if before_state else None,
            json.dumps(after_state, default=str),
            reason
        ))

    def upsert_asset(self, asset_data: Dict[str, Any], changed_by: str = "SYSTEM", reason: str = "Upsert") -> str:
        """Insert or update an asset, recording versioned history."""
        asset_id = asset_data["asset_id"]
        existing = self.conn.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,)).fetchone()
        
        if existing:
            current_version = existing[10]
            new_version = current_version + 1
            before_state = {
                "description": existing[5],
                "owner": existing[7],
                "certification_status": existing[8],
                "quality_score": existing[9],
                "version": current_version
            }
            self.conn.execute("""
                UPDATE assets SET
                    parent_id = COALESCE(?, parent_id),
                    asset_type = COALESCE(?, asset_type),
                    name = COALESCE(?, name),
                    display_name = COALESCE(?, display_name),
                    description = COALESCE(?, description),
                    data_type = COALESCE(?, data_type),
                    owner = COALESCE(?, owner),
                    certification_status = COALESCE(?, certification_status),
                    quality_score = COALESCE(?, quality_score),
                    version = ?,
                    updated_at = current_timestamp
                WHERE asset_id = ?
            """, (
                asset_data.get("parent_id"),
                asset_data.get("asset_type"),
                asset_data.get("name"),
                asset_data.get("display_name"),
                asset_data.get("description"),
                asset_data.get("data_type"),
                asset_data.get("owner"),
                asset_data.get("certification_status"),
                asset_data.get("quality_score"),
                new_version,
                asset_id
            ))
            self.record_history(
                asset_id=asset_id,
                version=new_version,
                change_type="UPDATE",
                changed_by=changed_by,
                before_state=before_state,
                after_state=asset_data,
                reason=reason
            )
        else:
            new_version = 1
            self.conn.execute("""
                INSERT INTO assets (
                    asset_id, parent_id, asset_type, name, display_name, description,
                    data_type, owner, certification_status, quality_score, version,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp, current_timestamp)
            """, (
                asset_id,
                asset_data.get("parent_id"),
                asset_data.get("asset_type", "TABLE"),
                asset_data.get("name", asset_id.split(".")[-1]),
                asset_data.get("display_name"),
                asset_data.get("description", ""),
                asset_data.get("data_type"),
                asset_data.get("owner", "Data Governance Guild"),
                asset_data.get("certification_status", "DRAFT"),
                asset_data.get("quality_score", 1.0),
                new_version
            ))
            self.record_history(
                asset_id=asset_id,
                version=new_version,
                change_type="CREATE",
                changed_by=changed_by,
                before_state=None,
                after_state=asset_data,
                reason=reason
            )
        return asset_id

    def add_tag(self, asset_id: str, tag_name: str, tag_value: Optional[str] = None,
                confidence: float = 1.0, source: str = "AGENT", reason: Optional[str] = None) -> str:
        """Attach a classification or governance tag to an asset."""
        tag_id = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO tags (tag_id, asset_id, tag_name, tag_value, confidence, source, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, current_timestamp)
        """, (tag_id, asset_id, tag_name, tag_value, confidence, source, reason))
        return tag_id

    def add_lineage_edge(self, source_asset_id: str, target_asset_id: str,
                         transformation_type: str = "TRANSFORMATION",
                         transformation_logic: Optional[str] = None) -> str:
        """Insert a lineage graph edge between two assets."""
        edge_id = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO lineage_edges (edge_id, source_asset_id, target_asset_id, transformation_type, transformation_logic, created_at)
            VALUES (?, ?, ?, ?, ?, current_timestamp)
        """, (edge_id, source_asset_id, target_asset_id, transformation_type, transformation_logic))
        return edge_id

    def populate_from_estate(self, estate_db_path: Optional[Path] = None):
        """Populate the catalog tables and columns from the real data estate."""
        e_path = estate_db_path or ESTATE_DB_PATH
        estate_conn = duckdb.connect(str(e_path))
        tables = estate_conn.execute("SHOW TABLES").fetchall()

        # Database node
        self.upsert_asset({
            "asset_id": "cforge",
            "asset_type": "DATABASE",
            "name": "cforge",
            "description": "ContextForge Central Data Estate",
            "certification_status": "CERTIFIED"
        })

        for (t_name,) in tables:
            table_asset_id = f"cforge.public.{t_name}"
            # Certify key production marts
            is_certified = "CERTIFIED" if (t_name.startswith("dim_") or t_name.startswith("fct_") or t_name.startswith("customer_ltv")) else "DRAFT"
            self.upsert_asset({
                "asset_id": table_asset_id,
                "parent_id": "cforge",
                "asset_type": "TABLE",
                "name": t_name,
                "display_name": t_name.replace("_", " ").title(),
                "certification_status": is_certified,
                "owner": "Analytics Engineering" if is_certified == "CERTIFIED" else "Data Engineering"
            })

            cols = estate_conn.execute(f"DESCRIBE {t_name}").fetchall()
            for col_name, col_type, *_ in cols:
                col_asset_id = f"{table_asset_id}.{col_name}"
                self.upsert_asset({
                    "asset_id": col_asset_id,
                    "parent_id": table_asset_id,
                    "asset_type": "COLUMN",
                    "name": col_name,
                    "data_type": col_type,
                    "certification_status": is_certified
                })

        # Load gold labels tags
        if GOLD_LABELS_PATH.exists():
            import csv
            with open(GOLD_LABELS_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    t_name = row["table_name"]
                    c_name = row["column_name"]
                    col_asset_id = f"cforge.public.{t_name}.{c_name}"
                    
                    # Update description if present
                    if row.get("true_business_description"):
                        self.conn.execute("UPDATE assets SET description = ? WHERE asset_id = ?",
                                          (row["true_business_description"], col_asset_id))
                    
                    # Add PII tag
                    if row.get("is_pii", "").lower() == "true":
                        self.add_tag(
                            asset_id=col_asset_id,
                            tag_name="PII",
                            tag_value=row.get("pii_type", "SENSITIVE"),
                            confidence=1.0,
                            source="GOLD_STANDARD",
                            reason="Ground truth gold label verified PII"
                        )
                    
                    # Add Glossary term mapping
                    if row.get("glossary_term"):
                        g_term = row["glossary_term"]
                        g_id = f"glossary.{g_term.lower().replace(' ', '_')}"
                        self.conn.execute("""
                            INSERT OR IGNORE INTO glossary_terms (term_id, term_name, definition, domain)
                            VALUES (?, ?, ?, 'Enterprise E-Commerce')
                        """, (g_id, g_term, f"Standard enterprise definition for {g_term}"))
                        self.conn.execute("""
                            INSERT OR IGNORE INTO asset_glossary_mappings (mapping_id, asset_id, term_id, confidence, mapped_by)
                            VALUES (?, ?, ?, 1.0, 'GOLD_STANDARD')
                        """, (str(uuid.uuid4()), col_asset_id, g_id))

        # Register downstream business dashboards consuming marts
        dashboards = [
            ("dashboard.executive_revenue", "Executive Revenue Overview", "fct_orders"),
            ("dashboard.customer_retention", "Customer Retention & LTV Hub", "customer_ltv"),
            ("dashboard.logistics_control_tower", "Logistics & SLA Tower", "mart_geo_performance"),
            ("dashboard.customer_360", "Customer 360 Profile", "dim_customers"),
        ]
        for d_id, d_name, upstream_tbl in dashboards:
            self.upsert_asset({
                "asset_id": d_id,
                "asset_type": "DASHBOARD",
                "name": d_name,
                "display_name": d_name,
                "certification_status": "CERTIFIED",
                "owner": "BI Analytics Team"
            })
            # Add table -> dashboard edge
            self.add_lineage_edge(
                source_asset_id=f"cforge.public.{upstream_tbl}",
                target_asset_id=d_id,
                transformation_type="DASHBOARD_CONSUMPTION",
                transformation_logic="Direct BI Visual Query"
            )

    def get_downstream_lineage_recursive(self, root_asset_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """Traverse downstream lineage graph using a recursive CTE."""
        query = f"""
            WITH RECURSIVE downstream_graph AS (
                -- Anchor member: direct targets of the root asset
                SELECT 
                    source_asset_id,
                    target_asset_id,
                    transformation_type,
                    1 AS depth,
                    CAST(source_asset_id || ' -> ' || target_asset_id AS VARCHAR) AS lineage_path
                FROM lineage_edges
                WHERE source_asset_id = ?

                UNION ALL

                -- Recursive member: follow targets downstream
                SELECT 
                    e.source_asset_id,
                    e.target_asset_id,
                    e.transformation_type,
                    g.depth + 1 AS depth,
                    CAST(g.lineage_path || ' -> ' || e.target_asset_id AS VARCHAR) AS lineage_path
                FROM lineage_edges e
                JOIN downstream_graph g ON e.source_asset_id = g.target_asset_id
                WHERE g.depth < {max_depth}
            )
            SELECT DISTINCT 
                target_asset_id,
                depth,
                lineage_path,
                transformation_type
            FROM downstream_graph
            ORDER BY depth, target_asset_id;
        """
        results = self.conn.execute(query, (root_asset_id,)).fetchall()
        return [
            {
                "target_asset_id": r[0],
                "depth": r[1],
                "lineage_path": r[2],
                "transformation_type": r[3]
            }
            for r in results
        ]

    def get_upstream_lineage_recursive(self, target_asset_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """Traverse upstream lineage graph using a recursive CTE."""
        query = f"""
            WITH RECURSIVE upstream_graph AS (
                -- Anchor member
                SELECT 
                    source_asset_id,
                    target_asset_id,
                    transformation_type,
                    1 AS depth,
                    CAST(target_asset_id || ' <- ' || source_asset_id AS VARCHAR) AS lineage_path
                FROM lineage_edges
                WHERE target_asset_id = ?

                UNION ALL

                -- Recursive member
                SELECT 
                    e.source_asset_id,
                    e.target_asset_id,
                    e.transformation_type,
                    g.depth + 1 AS depth,
                    CAST(g.lineage_path || ' <- ' || e.source_asset_id AS VARCHAR) AS lineage_path
                FROM lineage_edges e
                JOIN upstream_graph g ON e.target_asset_id = g.source_asset_id
                WHERE g.depth < {max_depth}
            )
            SELECT DISTINCT 
                source_asset_id,
                depth,
                lineage_path,
                transformation_type
            FROM upstream_graph
            ORDER BY depth, source_asset_id;
        """
        results = self.conn.execute(query, (target_asset_id,)).fetchall()
        return [
            {
                "source_asset_id": r[0],
                "depth": r[1],
                "lineage_path": r[2],
                "transformation_type": r[3]
            }
            for r in results
        ]
