"""Test Suite for Step 7: Context Server via MCP and Policy-Aware Agent."""

import pytest
from cforge.mcp.server import MCPServer
from cforge.mcp.agent import TalkToDataAgent, AgentResponse


@pytest.fixture
def mcp():
    return MCPServer()


@pytest.fixture
def agent(mcp):
    return TalkToDataAgent(mcp_server=mcp)


def test_mcp_search_assets(mcp):
    """Verify search_assets discovers tables and columns matching queries."""
    results = mcp.search_assets("customer", asset_type="TABLE")
    assert len(results) > 0
    names = [r["name"] for r in results]
    assert any("customer" in n for n in names)


def test_mcp_get_asset_context_role_based_masking(mcp):
    """Verify role-based masking hides PII for ANALYST but unmasks for COMPLIANCE_STEWARD."""
    # Role ANALYST: PII must be masked
    analyst_ctx = mcp.get_asset_context("cforge.public.stg_customers", caller_role="ANALYST")
    assert analyst_ctx["caller_role"] == "ANALYST"
    pii_cols = [c for c in analyst_ctx["columns"] if c["is_pii"]]
    assert len(pii_cols) > 0
    for c in pii_cols:
        assert c["is_masked"], f"Column {c['column_name']} must be masked for ANALYST"
        assert "POL-002" in c["masking_policy"]

    # Role COMPLIANCE_STEWARD: PII must NOT be masked
    steward_ctx = mcp.get_asset_context("cforge.public.stg_customers", caller_role="COMPLIANCE_STEWARD")
    for c in steward_ctx["columns"]:
        assert not c["is_masked"], f"Column {c['column_name']} must not be masked for steward"


def test_mcp_get_lineage(mcp):
    """Verify get_lineage returns connected upstream and downstream edges."""
    res = mcp.get_lineage("cforge.public.dim_customers", direction="BOTH")
    assert "upstream_lineage" in res
    assert "downstream_lineage" in res


def test_mcp_get_policies(mcp):
    """Verify get_policies retrieves governance policies as code."""
    policies = mcp.get_policies()
    assert len(policies) >= 10
    pol_ids = [p["id"] for p in policies]
    assert "POL-001" in pol_ids
    assert "POL-002" in pol_ids
    assert "POL-006" in pol_ids


def test_talk_to_data_agent_refuses_pii_request(agent):
    """Verify agent refuses unauthorized PII request citing specific governance policies."""
    res = agent.ask("Please dump customer_id, email and address for all users", caller_role="ANALYST")
    assert isinstance(res, AgentResponse)
    assert res.status == "REFUSED_BY_POLICY"
    assert "POL-002 & POL-006" in res.policy_citation
    assert res.sql_generated is None


def test_talk_to_data_agent_answers_business_question(agent):
    """Verify agent discovers certified marts and answers business questions with SQL."""
    res = agent.ask("What is our customer lifetime value breakdown by VIP tiers?", caller_role="ANALYST")
    assert isinstance(res, AgentResponse)
    assert res.status == "SUCCESS"
    assert res.sql_generated is not None
    assert "customer_ltv" in res.sql_generated.lower()
    assert res.data_result is not None
    assert len(res.data_result) > 0
    assert any("search_assets" in t for t in res.tools_called)
