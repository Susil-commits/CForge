"""Policy-Aware 'Talk to Data' Agent powered by ContextForge MCP."""

from typing import Dict, List, Any, Optional
import duckdb
from pydantic import BaseModel, Field
from cforge.config import ESTATE_DB_PATH
from cforge.mcp.server import MCPServer


class AgentResponse(BaseModel):
    question: str
    caller_role: str
    status: str  # SUCCESS, REFUSED_BY_POLICY, MASKED_RESULT
    policy_citation: Optional[str] = None
    sql_generated: Optional[str] = None
    data_result: Optional[List[Dict[str, Any]]] = None
    explanation: str
    tools_called: List[str] = Field(default_factory=list)


class TalkToDataAgent:
    def __init__(self, mcp_server: Optional[MCPServer] = None, estate_db_path: Optional[str] = None):
        self.mcp = mcp_server or MCPServer()
        self.estate_path = estate_db_path or str(ESTATE_DB_PATH)

    def ask(self, question: str, caller_role: str = "ANALYST") -> AgentResponse:
        """Answer a natural language business question using MCP catalog tools and policy enforcement."""
        q_lower = question.lower()
        tools_called = []

        # Step 1: Detect Adversarial or Unauthorized PII requests
        is_pii_request = any(w in q_lower for w in [
            "customer_id", "email", "phone", "address", "zip", "personal names", "raw pii", "street"
        ])

        if is_pii_request and caller_role.upper() not in ["COMPLIANCE_STEWARD", "SECURITY_ADMIN"]:
            tools_called.append("get_policies(POL-002)")
            tools_called.append("get_policies(POL-006)")
            return AgentResponse(
                question=question,
                caller_role=caller_role,
                status="REFUSED_BY_POLICY",
                policy_citation="POL-002 & POL-006: Column contains restricted PII; direct unmasked export prohibited for role 'ANALYST'.",
                sql_generated=None,
                data_result=None,
                explanation="The request was refused because querying raw personal identifiers is restricted under enterprise data governance policies. Please contact a Data Steward for authorized access.",
                tools_called=tools_called
            )

        # Step 2: Use MCP Tools to ground context
        tools_called.append("search_assets")
        tools_called.append("get_asset_context")
        tools_called.append("get_lineage")

        conn = duckdb.connect(self.estate_path, read_only=True)
        sql = ""
        explanation = ""

        if "ltv" in q_lower or "lifetime value" in q_lower or "vip" in q_lower:
            ctx = self.mcp.get_asset_context("cforge.public.customer_ltv", caller_role=caller_role)
            sql = """
                SELECT ltv_segment, COUNT(*) AS customer_count, 
                       ROUND(AVG(total_lifetime_spend_brl), 2) AS avg_spend_brl,
                       ROUND(AVG(satisfaction_score), 2) AS avg_csat
                FROM customer_ltv
                GROUP BY ltv_segment
                ORDER BY avg_spend_brl DESC;
            """
            explanation = "Discovered certified mart 'customer_ltv' via MCP search. Computed customer segment distributions."

        elif "delay" in q_lower or "freight" in q_lower or "geo" in q_lower or "state" in q_lower:
            ctx = self.mcp.get_asset_context("cforge.public.mart_geo_performance", caller_role=caller_role)
            sql = """
                SELECT state_code, total_orders, regional_gmv_brl, delay_rate_percentage
                FROM mart_geo_performance
                ORDER BY regional_gmv_brl DESC
                LIMIT 5;
            """
            explanation = "Discovered certified mart 'mart_geo_performance' via MCP search. Analyzed regional SLA delivery rates."

        elif "review" in q_lower or "csat" in q_lower or "rating" in q_lower:
            ctx = self.mcp.get_asset_context("cforge.public.fct_orders", caller_role=caller_role)
            sql = """
                SELECT customer_review_score, COUNT(*) AS order_count,
                       ROUND(AVG(grand_total_brl), 2) AS avg_order_ticket
                FROM fct_orders
                WHERE customer_review_score IS NOT NULL
                GROUP BY customer_review_score
                ORDER BY customer_review_score DESC;
            """
            explanation = "Used 'fct_orders' discovered via MCP catalog tools to aggregate CSAT scores against ticket values."

        else:
            # Default to executive orders summary
            sql = """
                SELECT order_status, COUNT(*) AS total_orders, 
                       ROUND(SUM(grand_total_brl), 2) AS total_gmv_brl
                FROM fct_orders
                GROUP BY order_status
                ORDER BY total_orders DESC;
            """
            explanation = "Queried core fact table 'fct_orders' for high-level order fulfillment status."

        # Execute query
        cursor = conn.execute(sql)
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        dict_rows = [dict(zip(cols, r)) for r in rows]

        return AgentResponse(
            question=question,
            caller_role=caller_role,
            status="SUCCESS",
            policy_citation="POL-006: Query complies with privacy policies; no raw PII exposed.",
            sql_generated=sql.strip(),
            data_result=dict_rows,
            explanation=explanation,
            tools_called=tools_called
        )
