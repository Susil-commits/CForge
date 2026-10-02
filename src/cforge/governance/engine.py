"""Policy-as-Code Evaluation Engine.

Evaluates YAML-defined policies prior to any catalog writes and flags violations or approval gates.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from cforge.config import POLICIES_PATH


class PolicyViolation(BaseModel):
    policy_id: str
    policy_name: str
    severity: str
    message: str
    blocked: bool


class PolicyEvaluationResult(BaseModel):
    passed: bool
    can_write: bool
    requires_approval: bool
    approval_reasons: List[str] = Field(default_factory=list)
    violations: List[PolicyViolation] = Field(default_factory=list)
    policies_checked_count: int


class PolicyEngine:
    def __init__(self, policies_file: Optional[Path] = None):
        self.policies_path = policies_file or POLICIES_PATH
        self.policies = self._load_policies()

    def _load_policies(self) -> List[Dict[str, Any]]:
        if not self.policies_path.exists():
            return []
        with open(self.policies_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("policies", [])

    def evaluate_write_proposal(self, proposal: Dict[str, Any]) -> PolicyEvaluationResult:
        """Evaluate a candidate write proposal against all active policies."""
        violations: List[PolicyViolation] = []
        approval_reasons: List[str] = []
        requires_approval = False
        blocked = False

        # Extract proposal fields
        description = proposal.get("description", "")
        sample_values = proposal.get("sample_values", [])
        is_pii = proposal.get("is_pii", False)
        pii_type = proposal.get("pii_type", "NONE")
        sensitivity = proposal.get("sensitivity_level", "INTERNAL")
        confidence = proposal.get("confidence", 1.0)
        certification_status = proposal.get("certification_status", "DRAFT")
        quality_score = proposal.get("quality_score", 1.0)
        owner = proposal.get("owner", None)
        null_rate = proposal.get("null_percentage", 0.0)
        has_quality_rules = proposal.get("quality_rules_count", 1) > 0
        is_mart = proposal.get("is_mart", False)

        for pol in self.policies:
            p_id = pol["id"]
            p_name = pol["name"]

            # POL-001: no_sample_values_in_descriptions
            if p_name == "no_sample_values_in_descriptions":
                if description and sample_values:
                    for s in sample_values:
                        s_str = str(s).strip()
                        if len(s_str) >= 4 and s_str.lower() in description.lower():
                            violations.append(PolicyViolation(
                                policy_id=p_id,
                                policy_name=p_name,
                                severity="CRITICAL",
                                message=f"Description contains raw sample value '{s_str}'.",
                                blocked=True
                            ))
                            blocked = True

            # POL-002: pii_requires_steward_approval
            elif p_name == "pii_requires_steward_approval":
                if is_pii:
                    requires_approval = True
                    approval_reasons.append("Asset contains PII; steward sign-off required before active write.")

            # POL-003: agent_confidence_threshold
            elif p_name == "agent_confidence_threshold":
                thresh = pol.get("threshold", 0.80)
                if confidence < thresh:
                    requires_approval = True
                    approval_reasons.append(f"Agent confidence ({confidence:.2f}) below policy threshold ({thresh}).")

            # POL-004: certification_quality_gate
            elif p_name == "certification_quality_gate":
                min_q = pol.get("min_quality_score", 0.85)
                if certification_status == "CERTIFIED" and quality_score < min_q:
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="HIGH",
                        message=f"Certification requires quality score >= {min_q}, current is {quality_score}.",
                        blocked=True
                    ))
                    blocked = True

            # POL-005: certification_owner_mandatory
            elif p_name == "certification_owner_mandatory":
                if certification_status == "CERTIFIED" and (not owner or owner.strip() == ""):
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="HIGH",
                        message="Asset cannot be CERTIFIED without a designated owner.",
                        blocked=True
                    ))
                    blocked = True

            # POL-006: restricted_pii_no_public_access
            elif p_name == "restricted_pii_no_public_access":
                if is_pii and sensitivity == "PUBLIC":
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="CRITICAL",
                        message="PII tagged columns cannot be marked as PUBLIC sensitivity.",
                        blocked=True
                    ))
                    blocked = True

            # POL-009: prohibit_empty_descriptions
            elif p_name == "prohibit_empty_descriptions":
                if "description" in proposal and len(proposal["description"].strip()) == 0:
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="MEDIUM",
                        message="Description cannot be empty whitespace.",
                        blocked=True
                    ))
                    blocked = True

            # POL-010: enforce_valid_pii_types
            elif p_name == "enforce_valid_pii_types":
                allowed = pol.get("allowed_types", [])
                if is_pii and pii_type not in allowed:
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="HIGH",
                        message=f"PII type '{pii_type}' not in allowed taxonomy: {allowed}.",
                        blocked=True
                    ))
                    blocked = True

            # POL-011: high_null_rate_certification_block
            elif p_name == "high_null_rate_certification_block":
                max_null = pol.get("max_null_rate", 95.0)
                if certification_status == "CERTIFIED" and null_rate > max_null:
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="HIGH",
                        message=f"Null rate ({null_rate}%) exceeds threshold ({max_null}%) for certified asset.",
                        blocked=True
                    ))
                    blocked = True

            # POL-014: quality_rule_coverage_for_marts
            elif p_name == "quality_rule_coverage_for_marts":
                if is_mart and not has_quality_rules:
                    violations.append(PolicyViolation(
                        policy_id=p_id,
                        policy_name=p_name,
                        severity="MEDIUM",
                        message="Production analytics mart must have at least one quality validation rule.",
                        blocked=True
                    ))
                    blocked = True

        can_write = not blocked and not requires_approval
        passed = (len(violations) == 0)

        return PolicyEvaluationResult(
            passed=passed,
            can_write=can_write,
            requires_approval=requires_approval,
            approval_reasons=approval_reasons,
            violations=violations,
            policies_checked_count=len(self.policies)
        )
