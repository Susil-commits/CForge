"""Model Context Protocol (MCP) Server for Governed Catalog Context.

Exposes search_assets, get_asset_context, get_lineage, get_policies, and get_quality.
Enforces role-based masking and policy citations for unauthorized callers.
"""

from typing import Any

from cforge.catalog.store import MetadataStore
from cforge.governance.engine import PolicyEngine


class MCPServer:
    def __init__(self, metadata_db_path: Any | None = None, store: MetadataStore | None = None):
        self.store = store or MetadataStore(metadata_db_path, auto_populate=True)
        self.policy_engine = PolicyEngine()

    def search_assets(self, query: str, asset_type: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Search catalog assets with multi-term semantic token scoring and certified boost."""
        tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
        if not tokens:
            tokens = [query.strip().lower()]

        type_filter = "AND asset_type = ?" if asset_type else ""
        sql = f"""
            SELECT asset_id, asset_type, name, display_name, description, certification_status, owner
            FROM assets
            WHERE 1=1 {type_filter};
        """
        params = [asset_type.upper()] if asset_type else []

        with self.store.lock:
            rows = self.store.conn.execute(sql, params).fetchall()

        q_lower = query.lower()
        scored_results = []
        for r in rows:
            name_lower = (r[2] or "").lower()
            desc_lower = (r[4] or "").lower()
            score = 0.0

            # Exact phrase matches
            if q_lower in name_lower:
                score += 50.0
            if q_lower in desc_lower:
                score += 25.0

            # Token overlap scoring
            for token in tokens:
                if token in name_lower:
                    score += 20.0
                if token in desc_lower:
                    score += 10.0

            # Certified tier boost (production-ready marts get priority)
            if r[5] == "CERTIFIED":
                score += 15.0

            if score > 0:
                scored_results.append(
                    (
                        score,
                        {
                            "asset_id": r[0],
                            "asset_type": r[1],
                            "name": r[2],
                            "display_name": r[3],
                            "description": r[4],
                            "certification_status": r[5],
                            "owner": r[6],
                            "relevance_score": round(score, 2),
                        },
                    )
                )

        # Sort by relevance score descending, then alphabetically by name
        scored_results.sort(key=lambda x: (-x[0], x[1]["name"]))
        return [item for _, item in scored_results[:limit]]

    def get_asset_context(self, asset_id: str, caller_role: str = "ANALYST") -> dict[str, Any]:
        """Fetch rich context for an asset, applying role-based PII masking and policy citations."""
        with self.store.lock:
            asset = self.store.conn.execute(
                """
                SELECT asset_id, parent_id, asset_type, name, display_name, description, data_type, owner, certification_status, quality_score, version
                FROM assets WHERE asset_id = ?
            """,
                (str(asset_id),),
            ).fetchone()

            if not asset:
                raise KeyError(f"Asset '{asset_id}' not found in ContextForge catalog.")

            # Get tags
            tag_rows = self.store.conn.execute(
                """
                SELECT tag_name, tag_value, confidence, source, reason
                FROM tags WHERE asset_id = ?
            """,
                (str(asset_id),),
            ).fetchall()
            tags = [{"name": t[0], "value": t[1], "confidence": t[2], "source": t[3], "reason": t[4]} for t in tag_rows]

            # Get columns if it's a table
            columns = []
            if asset[2] == "TABLE":
                col_rows = self.store.conn.execute(
                    """
                    SELECT asset_id, name, description, data_type, certification_status
                    FROM assets WHERE parent_id = ? AND asset_type = 'COLUMN'
                """,
                    (str(asset_id),),
                ).fetchall()

                for c in col_rows:
                    c_id = str(c[0])
                    c_tags = self.store.conn.execute(
                        "SELECT tag_name, tag_value FROM tags WHERE asset_id = ?", (c_id,)
                    ).fetchall()
                    is_pii = any(t[0] == "PII" for t in c_tags)
                    pii_type = next((t[1] for t in c_tags if t[0] == "PII"), "NONE")

                    # Role-based masking: analysts cannot see unmasked PII
                    is_masked = False
                    masking_policy = None
                    if is_pii and caller_role.upper() not in ["COMPLIANCE_STEWARD", "SECURITY_ADMIN"]:
                        is_masked = True
                        masking_policy = "POL-002 & POL-006: PII restricted from unauthorized role access."

                    columns.append(
                        {
                            "column_asset_id": c_id,
                            "column_name": c[1],
                            "description": c[2],
                            "data_type": c[3],
                            "is_pii": is_pii,
                            "pii_type": pii_type,
                            "is_masked": is_masked,
                            "masking_policy": masking_policy,
                        }
                    )

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
            "caller_role": caller_role,
        }

    def get_lineage(self, asset_id: str, direction: str = "BOTH", max_depth: int = 5) -> dict[str, Any]:
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
            "downstream_lineage": downstream,
        }

    def get_policies(self, policy_id: str | None = None) -> list[dict[str, Any]]:
        """List active governance policies as code."""
        if policy_id:
            return [p for p in self.policy_engine.policies if p["id"] == policy_id]
        return self.policy_engine.policies

    def get_quality(self, table_name: str) -> dict[str, Any]:
        """Fetch quality score and validation state for an asset."""
        table_asset = f"cforge.public.{table_name}"
        res = self.store.conn.execute(
            "SELECT quality_score, certification_status FROM assets WHERE asset_id = ?", (table_asset,)
        ).fetchone()
        if not res:
            return {"table_name": table_name, "quality_score": 1.0, "status": "UNKNOWN"}
        return {
            "table_name": table_name,
            "asset_id": table_asset,
            "quality_score": res[0],
            "certification_status": res[1],
        }

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        """Returns standard Model Context Protocol (MCP) tool schemas for discovery."""
        return [
            {
                "name": "search_assets",
                "description": "Search catalog assets by keywords, natural business terms, or domain tags.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search keywords (e.g. 'customer', 'revenue', 'order')",
                        },
                        "asset_type": {
                            "type": "string",
                            "enum": ["TABLE", "COLUMN", "DASHBOARD"],
                            "description": "Filter by asset type",
                        },
                        "limit": {"type": "integer", "default": 10, "description": "Max results to return"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_asset_context",
                "description": "Fetch schema, semantic descriptions, certified status, and columns for an asset with role-based PII masking.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "Full asset identifier (e.g. 'cforge.public.dim_customers')",
                        },
                        "caller_role": {
                            "type": "string",
                            "default": "ANALYST",
                            "enum": ["ANALYST", "COMPLIANCE_STEWARD", "SECURITY_ADMIN"],
                        },
                    },
                    "required": ["asset_id"],
                },
            },
            {
                "name": "get_lineage",
                "description": "Retrieve upstream and downstream dependency graph for an asset across data pipelines.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "asset_id": {"type": "string", "description": "Asset ID to trace lineage for"},
                        "direction": {"type": "string", "enum": ["UPSTREAM", "DOWNSTREAM", "BOTH"], "default": "BOTH"},
                        "max_depth": {"type": "integer", "default": 5},
                    },
                    "required": ["asset_id"],
                },
            },
            {
                "name": "get_policies",
                "description": "List enterprise governance policies as code, including PII constraints and certification thresholds.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_id": {"type": "string", "description": "Optional specific policy ID (e.g. 'POL-002')"}
                    },
                },
            },
            {
                "name": "get_quality",
                "description": "Fetch data quality metrics, defect rates, and certification status for a table.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Bare or schema-qualified table name (e.g. 'fct_orders')",
                        }
                    },
                    "required": ["table_name"],
                },
            },
        ]


# Architectural alias: ContextForge's in-process MCP Context Gateway
MCPContextGateway = MCPServer
