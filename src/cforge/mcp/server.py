"""Model Context Protocol (MCP) Server for Governed Catalog Context.

Exposes search_assets, get_asset_context, get_lineage, get_policies, and get_quality.
Enforces role-based masking and policy citations for unauthorized callers.
"""

from typing import Dict, List, Any, Optional
import duckdb
from pydantic import BaseModel, Field
from cforge.config import ESTATE_DB_PATH, METADATA_DB_PATH
from cforge.catalog.store import MetadataStore
from cforge.governance.engine import PolicyEngine


class MCPServer:
    def __init__(self, metadata_db_path: Optional[str] = None):
        self.store = MetadataStore(metadata_db_path)
        self.policy_engine = PolicyEngine()

    def search_assets(self, query: str, asset_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search catalog assets by name, description, or tags."""
        q = f"%{query.lower()}%"
        type_filter = "AND asset_type = ?" if asset_type else ""
        sql = f"""
            SELECT asset_id, asset_type, name, display_name, description, certification_status, owner
            FROM assets
            WHERE (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)
            {type_filter}
            ORDER BY 
                CASE WHEN certification_status = 'CERTIFIED' THEN 1 ELSE 2 END,
                name
            LIMIT ?;
        """
        params = [q, q]
        if asset_type:
            params.append(asset_type.upper())
        params.append(limit)

        rows = self.store.conn.execute(sql, params).fetchall()
        return [
            {
                "asset_id": r[0],
                "asset_type": r[1],
                "name": r[2],
                "display_name": r[3],
                "description": r[4],
                "certification_status": r[5],
                "owner": r[6]
            }
            for r in rows
        ]

    def get_asset_context(self, asset_id: str, caller_role: str = "ANALYST") -> Dict[str, Any]:
        """Fetch rich context for an asset, applying role-based PII masking and policy citations."""
        asset = self.store.conn.execute("""
            SELECT asset_id, parent_id, asset_type, name, display_name, description, data_type, owner, certification_status, quality_score, version
            FROM assets WHERE asset_id = ?
        """, (asset_id,)).fetchone()

        if not asset:
            raise KeyError(f"Asset '{asset_id}' not found in ContextForge catalog.")

        # Get tags
        tag_rows = self.store.conn.execute("""
            SELECT tag_name, tag_value, confidence, source, reason
            FROM tags WHERE asset_id = ?
        """, (asset_id,)).fetchall()
        tags = [{"name": t[0], "value": t[1], "confidence": t[2], "source": t[3], "reason": t[4]} for t in tag_rows]

        # Get columns if it's a table
        columns = []
        if asset[2] == "TABLE":
            col_rows = self.store.conn.execute("""
                SELECT asset_id, name, description, data_type, certification_status
                FROM assets WHERE parent_id = ? AND asset_type = 'COLUMN'
            """, (asset_id,)).fetchall()
            
            for c in col_rows:
                c_id = c[0]
                c_tags = self.store.conn.execute("SELECT tag_name, tag_value FROM tags WHERE asset_id = ?", (c_id,)).fetchall()
                is_pii = any(t[0] == "PII" for t in c_tags)
                pii_type = next((t[1] for t in c_tags if t[0] == "PII"), "NONE")

                # Role-based masking: analysts cannot see unmasked PII
                is_masked = False
                masking_policy = None
                if is_pii and caller_role.upper() not in ["COMPLIANCE_STEWARD", "SECURITY_ADMIN"]:
                    is_masked = True
                    masking_policy = "POL-002 & POL-006: PII restricted from unauthorized role access."

                columns.append({
                    "column_asset_id": c_id,
                    "column_name": c[1],
                    "description": c[2],
                    "data_type": c[3],
                    "is_pii": is_pii,
                    "pii_type": pii_type,
                    "is_masked": is_masked,
                    "masking_policy": masking_policy
                })

        return {
            "asset_id": asset[0],
            "parent_id": asset[1],
            "asset_type": asset[2],
            "name": asset[3],
            "display_name": asset[4],
            "description": asset[5],
            "data_type": asset[6],
            "owner": asset[7],
            "certification_status": asset[8],
            "quality_score": asset[9],
            "version": asset[10],
            "tags": tags,
            "columns": columns,
            "caller_role": caller_role
        }

    def get_lineage(self, asset_id: str, direction: str = "BOTH", max_depth: int = 5) -> Dict[str, Any]:
        """Fetch upstream and downstream lineage graph."""
        upstream = []
        downstream = []
        if direction.upper() in ["UPSTREAM", "BOTH"]:
            upstream = self.store.get_upstream_lineage_recursive(asset_id, max_depth=max_depth)
        if direction.upper() in ["DOWNSTREAM", "BOTH"]:
            downstream = self.store.get_downstream_lineage_recursive(asset_id, max_depth=max_depth)

        return {
            "asset_id": asset_id,
            "upstream_count": len(upstream),
            "downstream_count": len(downstream),
            "upstream_lineage": upstream,
            "downstream_lineage": downstream
        }

    def get_policies(self, policy_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active governance policies as code."""
        if policy_id:
            return [p for p in self.policy_engine.policies if p["id"] == policy_id]
        return self.policy_engine.policies

    def get_quality(self, table_name: str) -> Dict[str, Any]:
        """Fetch quality score and validation state for an asset."""
        table_asset = f"cforge.public.{table_name}"
        res = self.store.conn.execute("SELECT quality_score, certification_status FROM assets WHERE asset_id = ?", (table_asset,)).fetchone()
        if not res:
            return {"table_name": table_name, "quality_score": 1.0, "status": "UNKNOWN"}
        return {
            "table_name": table_name,
            "asset_id": table_asset,
            "quality_score": res[0],
            "certification_status": res[1]
        }
