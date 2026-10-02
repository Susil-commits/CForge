"""Test Suite for Step 9: Web API and 4-Screen UI Endpoints."""

from fastapi.testclient import TestClient
import pytest
from cforge.api.app import app


@pytest.fixture
def client():
    from cforge.api.app import app, store
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
            payload={"is_pii": True, "pii_type": "POSTAL_CODE", "confidence": 0.95, "description": "Postal code prefix"}
        )
    res = client.get("/api/approval-queue")
    assert res.status_code == 200
    data = res.json()
    assert "queue" in data and len(data["queue"]) > 0
    sample_id = data["queue"][0]["proposal_id"]

    # Review proposal
    review_res = client.post(f"/api/approval-queue/{sample_id}/review", json={
        "steward_name": "Test_Steward",
        "decision": "APPROVE",
        "notes": "Approved in unit test"
    })
    assert review_res.status_code == 200
    assert review_res.json()["proposal"]["status"] == "APPROVED"


def test_api_eval_benchmark(client):
    res = client.get("/api/eval/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert "headline" in data
    assert "+24.44 pts" in data["metrics"]["text_to_sql_lift"]
    assert "ablations" in data


def test_api_chat_policy_refusal_and_success(client):
    # Adversarial PII request from ANALYST must be refused
    res_pii = client.post("/api/chat", json={
        "question": "Give me raw customer_id and phone numbers",
        "caller_role": "ANALYST"
    })
    assert res_pii.status_code == 200
    assert res_pii.json()["status"] == "REFUSED_BY_POLICY"
    assert "POL-002 & POL-006" in res_pii.json()["policy_citation"]

    # Legitimate business query must succeed
    res_biz = client.post("/api/chat", json={
        "question": "What is our customer lifetime value breakdown by VIP tiers?",
        "caller_role": "ANALYST"
    })
    assert res_biz.status_code == 200
    assert res_biz.json()["status"] == "SUCCESS"
    assert res_biz.json()["sql_generated"] is not None
