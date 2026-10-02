"""Test Suite for Step 5: Governance Layer and Policy-as-Code.

Includes 16+ distinct policy test cases and 3-hop lineage tag propagation proof.
"""

import pytest
from cforge.governance.engine import PolicyEngine
from cforge.governance.approval import ApprovalQueue
from cforge.governance.audit import ImmutableAuditLog
from cforge.lineage.parser import ColumnLineageEdge
from cforge.lineage.propagator import LineagePropagator


@pytest.fixture
def engine():
    return PolicyEngine()


@pytest.fixture
def queue(engine):
    return ApprovalQueue(engine)


# --- Policy Case 1 & 2: POL-001 No Sample Values in Descriptions ---
def test_pol_001_sample_value_in_description_blocked(engine):
    proposal = {
        "description": "Customer record with email test.user@example.com in account.",
        "sample_values": ["test.user@example.com", "other@domain.com"],
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert not result.can_write
    assert any(v.policy_id == "POL-001" for v in result.violations)


def test_pol_001_clean_description_allowed(engine):
    proposal = {
        "description": "General customer account entity identifier.",
        "sample_values": ["c9837248bde", "83742918a"],
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not any(v.policy_id == "POL-001" for v in result.violations)


# --- Policy Case 3 & 4: POL-002 PII Requires Steward Approval ---
def test_pol_002_pii_triggers_steward_approval(engine):
    proposal = {
        "description": "Customer permanent identity token.",
        "is_pii": True,
        "pii_type": "CUSTOMER_ID",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert result.requires_approval
    assert not result.can_write
    assert any("PII" in r for r in result.approval_reasons)


def test_pol_002_non_pii_does_not_require_steward_approval(engine):
    proposal = {
        "description": "Total merchandise item weight in grams.",
        "is_pii": False,
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.requires_approval
    assert result.can_write


# --- Policy Case 5 & 6: POL-003 Agent Confidence Threshold ---
def test_pol_003_low_confidence_requires_review(engine):
    proposal = {
        "description": "Inferred customer segment.",
        "confidence": 0.65
    }
    result = engine.evaluate_write_proposal(proposal)
    assert result.requires_approval
    assert not result.can_write
    assert any("threshold" in r for r in result.approval_reasons)


def test_pol_003_high_confidence_passes(engine):
    proposal = {
        "description": "Inferred customer segment.",
        "confidence": 0.92
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.requires_approval


# --- Policy Case 7 & 8: POL-004 Certification Quality Score Gate ---
def test_pol_004_certification_blocked_on_low_quality(engine):
    proposal = {
        "certification_status": "CERTIFIED",
        "quality_score": 0.72,
        "owner": "Data Governance Team",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert not result.can_write
    assert any(v.policy_id == "POL-004" for v in result.violations)


def test_pol_004_certification_allowed_on_high_quality(engine):
    proposal = {
        "certification_status": "CERTIFIED",
        "quality_score": 0.94,
        "owner": "Data Governance Team",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not any(v.policy_id == "POL-004" for v in result.violations)


# --- Policy Case 9 & 10: POL-005 Certification Owner Mandatory ---
def test_pol_005_certification_blocked_without_owner(engine):
    proposal = {
        "certification_status": "CERTIFIED",
        "quality_score": 0.95,
        "owner": "",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert any(v.policy_id == "POL-005" for v in result.violations)


# --- Policy Case 11 & 12: POL-006 Restricted PII No Public Access ---
def test_pol_006_pii_with_public_sensitivity_blocked(engine):
    proposal = {
        "is_pii": True,
        "pii_type": "CUSTOMER_ID",
        "sensitivity_level": "PUBLIC",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert any(v.policy_id == "POL-006" for v in result.violations)


# --- Policy Case 13: POL-009 Prohibit Empty Descriptions ---
def test_pol_009_empty_description_blocked(engine):
    proposal = {
        "description": "   ",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert any(v.policy_id == "POL-009" for v in result.violations)


# --- Policy Case 14: POL-010 Enforce Valid PII Taxonomy Types ---
def test_pol_010_invalid_pii_type_blocked(engine):
    proposal = {
        "is_pii": True,
        "pii_type": "UNKNOWN_CUSTOM_TAXONOMY",
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert any(v.policy_id == "POL-010" for v in result.violations)


# --- Policy Case 15: POL-011 High Null Rate Blocks Certification ---
def test_pol_011_high_null_rate_blocks_certification(engine):
    proposal = {
        "certification_status": "CERTIFIED",
        "owner": "Finance Team",
        "quality_score": 0.90,
        "null_percentage": 98.5,
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert any(v.policy_id == "POL-011" for v in result.violations)


# --- Policy Case 16: POL-014 Mart Quality Coverage ---
def test_pol_014_mart_without_rules_blocked(engine):
    proposal = {
        "is_mart": True,
        "quality_rules_count": 0,
        "confidence": 0.95
    }
    result = engine.evaluate_write_proposal(proposal)
    assert not result.passed
    assert any(v.policy_id == "POL-014" for v in result.violations)


# --- Approval Queue & Steward Review Lifecycle ---
def test_approval_queue_lifecycle(queue):
    # Auto-approve path
    auto_prop = queue.submit_proposal(
        asset_id="cforge.public.dim_products.weight_class",
        change_type="UPDATE_DESCRIPTION",
        proposed_by="Agent_Describer",
        payload={"description": "Weight tier classification.", "confidence": 0.95}
    )
    assert auto_prop.status == "AUTO_APPROVED"

    # Queue review path
    review_prop = queue.submit_proposal(
        asset_id="cforge.public.dim_customers.primary_zip",
        change_type="ADD_TAG",
        proposed_by="Agent_Classifier",
        payload={"is_pii": True, "pii_type": "POSTAL_CODE", "confidence": 0.95}
    )
    assert review_prop.status == "PENDING"
    assert len(queue.get_pending()) >= 1

    # Steward approves
    reviewed = queue.review_proposal(
        proposal_id=review_prop.proposal_id,
        steward_name="Governance_Steward_Alice",
        decision="APPROVE",
        notes="Confirmed Brazilian CEP postal code is PII."
    )
    assert reviewed.status == "APPROVED"
    assert reviewed.reviewed_by == "Governance_Steward_Alice"


# --- Immutable Cryptographic Audit Log ---
def test_immutable_audit_log_hash_chain():
    audit = ImmutableAuditLog()
    assert audit.verify_integrity()

    # Append events
    audit.append("Agent_1", "asset_1", "PROPOSE_DESC", ["POL-001"], None, {"desc": "v1"})
    audit.append("Steward_Bob", "asset_1", "APPROVE", ["POL-002"], {"desc": "v1"}, {"desc": "v1", "status": "APPROVED"})

    assert len(audit.chain) == 3
    assert audit.verify_integrity()

    # Tampering test: modify an entry and verify integrity failure
    audit.chain[1].actor = "MALICIOUS_ACTOR"
    assert not audit.verify_integrity(), "Tampered log must fail cryptographic integrity!"


# --- Multi-Hop Tag Propagation Proof Across 3 Hops ---
def test_tag_propagation_across_3_hops_with_reason_chain():
    # Model 3 hops: raw_olist_customers -> stg_customers -> dim_customers -> customer_ltv
    edges = [
        ColumnLineageEdge("raw_olist_customers", "customer_id", "stg_customers", "customer_id", "DIRECT_COPY"),
        ColumnLineageEdge("stg_customers", "customer_id", "dim_customers", "customer_unique_id", "AGGREGATION"),
        ColumnLineageEdge("dim_customers", "customer_unique_id", "customer_ltv", "customer_unique_id", "DIRECT_COPY")
    ]
    propagator = LineagePropagator(edges)
    results = propagator.propagate_tag(
        initial_table="raw_olist_customers",
        initial_column="customer_id",
        tag_name="PII",
        tag_value="CUSTOMER_ID",
        max_hops=5
    )

    # Verify Hop 1, Hop 2, Hop 3 exist
    hops = {p.hop_count: p for p in results}
    assert 1 in hops, "Missing Hop 1"
    assert 2 in hops, "Missing Hop 2"
    assert 3 in hops, "Missing Hop 3"

    hop3 = hops[3]
    assert hop3.target_table == "customer_ltv"
    assert hop3.target_column == "customer_unique_id"
    assert hop3.tag_name == "PII"
    assert hop3.tag_value == "CUSTOMER_ID"
    assert len(hop3.reason_chain) == 4  # Root + 3 hops
    assert "raw_olist_customers.customer_id" in hop3.reason_chain[0]
    assert "stg_customers.customer_id" in hop3.reason_chain[1]
    assert "dim_customers.customer_unique_id" in hop3.reason_chain[2]
    assert "customer_ltv.customer_unique_id" in hop3.reason_chain[3]
