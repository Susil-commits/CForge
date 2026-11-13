"""Test Suite for Step 9: Web API and 4-Screen UI Endpoints."""

import pytest
from fastapi.testclient import TestClient

from cforge.api.app import app


@pytest.fixture
def client():
    from cforge.api.app import store

    if store.conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0:
        store.populate_from_estate()
    return TestClient(app)


def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_api_lineage_graph(client):
    res = client.get("/api/lineage")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data and len(data["nodes"]) > 0
    assert "edges" in data and len(data["edges"]) > 0
    # Verify PII node exists
    assert any(n["has_pii"] for n in data["nodes"])


def test_api_list_assets(client):
    res = client.get("/api/assets")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert len(data["assets"]) > 0


def test_api_approval_queue_lifecycle(client):
    from cforge.api.app import approval_queue

    if len(approval_queue.get_pending()) == 0:
        approval_queue.submit_proposal(
            asset_id="cforge.public.dim_customers.primary_zip",
            change_type="ADD_TAG",
            proposed_by="Agent_Classifier",
            payload={
                "is_pii": True,
                "pii_type": "POSTAL_CODE",
                "confidence": 0.95,
                "description": "Postal code prefix",
            },
        )
    res = client.get("/api/approval-queue")
    assert res.status_code == 200
    data = res.json()
    assert "queue" in data and len(data["queue"]) > 0
    sample_id = data["queue"][0]["proposal_id"]

    # Review proposal
    review_res = client.post(
        f"/api/approval-queue/{sample_id}/review",
        json={"steward_name": "Test_Steward", "decision": "APPROVE", "notes": "Approved in unit test"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["proposal"]["status"] == "APPROVED"


def test_api_eval_benchmark(client):
    res = client.get("/api/eval/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert "headline" in data
    assert "+22.23 pts" in data["metrics"]["text_to_sql_lift"] or "pts" in data["metrics"]["text_to_sql_lift"]
    assert "ablations" in data


def test_api_chat_policy_refusal_and_success(client):
    # Adversarial PII request from ANALYST must be refused
    res_pii = client.post(
        "/api/chat", json={"question": "Give me raw customer_id and phone numbers", "caller_role": "ANALYST"}
    )
    assert res_pii.status_code == 200
    assert res_pii.json()["status"] == "REFUSED_BY_POLICY"
    assert "POL-002 & POL-006" in res_pii.json()["policy_citation"]

    # Legitimate business query must succeed
    res_biz = client.post(
        "/api/chat",
        json={"question": "What is our customer lifetime value breakdown by VIP tiers?", "caller_role": "ANALYST"},
    )
    assert res_biz.status_code == 200
    assert res_biz.json()["status"] == "SUCCESS"
    assert res_biz.json()["sql_generated"] is not None


def test_api_audit_trail_and_chain_integrity(client):
    res = client.get("/api/governance/audit-trail")
    assert res.status_code == 200
    data = res.json()
    assert "chain_length" in data
    assert data["integrity_verified"] is True
    assert data["genesis_root"] is not None
    assert len(data["records"]) > 0


def test_api_steward_role_auth_gate(client):
    from cforge.config import STEWARD_ACCESS_TOKEN

    # 1. Unauthenticated COMPLIANCE_STEWARD role request (downgraded to ANALYST)
    res_unauth = client.post(
        "/api/chat", json={"question": "Give me raw customer_id and phone numbers", "caller_role": "COMPLIANCE_STEWARD"}
    )
    assert res_unauth.status_code == 200
    # Must be refused because unauthorized steward is safely downgraded to ANALYST
    assert res_unauth.json()["status"] == "REFUSED_BY_POLICY"
    assert "auth_warning" in res_unauth.json()

    # 2. Authenticated COMPLIANCE_STEWARD request with valid token
    res_auth = client.post(
        "/api/chat",
        json={
            "question": "Give me raw customer_id and phone numbers",
            "caller_role": "COMPLIANCE_STEWARD",
            "steward_token": STEWARD_ACCESS_TOKEN,
        },
    )
    assert res_auth.status_code == 200
    # With valid token, request is not refused under POL-002 role restriction
    assert res_auth.json()["status"] != "REFUSED_BY_POLICY"


def test_api_proposal_approval_mutates_catalog(client):
    from cforge.api.app import approval_queue, store

    test_col = "cforge.public.stg_products.product_category_name"
    prop = approval_queue.submit_proposal(
        asset_id=test_col,
        change_type="ADD_TAG",
        proposed_by="Agent_Classifier",
        payload={"is_pii": False, "tag_name": "DOMAIN", "tag_value": "ECOMMERCE_CATALOG", "confidence": 0.99},
    )

    review_res = client.post(
        f"/api/approval-queue/{prop.proposal_id}/review",
        json={
            "steward_name": "Senior_Data_Steward",
            "decision": "APPROVE",
            "notes": "Verified by steward in catalog mutation test",
        },
    )
    assert review_res.status_code == 200
    assert review_res.json()["proposal"]["status"] == "APPROVED"

    # Verify catalog actually received the tag!
    with store.lock:
        tag = store.conn.execute(
            "SELECT tag_name, tag_value FROM tags WHERE asset_id = ? AND tag_name = 'DOMAIN'", (test_col,)
        ).fetchone()
        assert tag is not None
        assert tag[0] == "DOMAIN"
        assert tag[1] == "ECOMMERCE_CATALOG"


def test_api_governance_policies(client):
    res = client.get("/api/governance/policies")
    assert res.status_code == 200
    data = res.json()
    assert "policies" in data
    assert data["total_policies"] >= 5
    ids = [p["id"] for p in data["policies"]]
    assert "POL-001" in ids
    assert "POL-002" in ids
