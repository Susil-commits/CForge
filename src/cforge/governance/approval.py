"""Approval Queue for Governed Metadata Changes."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field
from cforge.governance.engine import PolicyEngine, PolicyEvaluationResult


class ChangeProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_id: str
    change_type: str  # UPDATE_DESCRIPTION, ADD_TAG, CHANGE_CERTIFICATION, PROPOSE_RULE
    proposed_by: str
    payload: Dict[str, Any]
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, AUTO_APPROVED
    evaluation: Optional[PolicyEvaluationResult] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalQueue:
    def __init__(self, engine: Optional[PolicyEngine] = None):
        self.engine = engine or PolicyEngine()
        self.queue: Dict[str, ChangeProposal] = {}

    def submit_proposal(self, asset_id: str, change_type: str,
                        proposed_by: str, payload: Dict[str, Any]) -> ChangeProposal:
        """Submit a proposal, evaluate policies, and either auto-approve or queue for review."""
        eval_result = self.engine.evaluate_write_proposal(payload)
        
        proposal = ChangeProposal(
            asset_id=asset_id,
            change_type=change_type,
            proposed_by=proposed_by,
            payload=payload,
            evaluation=eval_result
        )

        if eval_result.can_write:
            proposal.status = "AUTO_APPROVED"
            proposal.reviewed_by = "POLICY_ENGINE_AUTO"
            proposal.reviewed_at = datetime.now(timezone.utc)
            proposal.review_notes = "All policy gates passed with high confidence; auto-approved."
        elif not eval_result.passed:
            proposal.status = "REJECTED"
            proposal.reviewed_by = "POLICY_ENGINE_GATE"
            proposal.reviewed_at = datetime.now(timezone.utc)
            proposal.review_notes = f"Blocked by policies: {[v.message for v in eval_result.violations]}"
        else:
            proposal.status = "PENDING"

        self.queue[proposal.proposal_id] = proposal
        return proposal

    def get_pending(self) -> List[ChangeProposal]:
        """List all proposals currently waiting for human steward review."""
        return [p for p in self.queue.values() if p.status == "PENDING"]

    def review_proposal(self, proposal_id: str, steward_name: str,
                        decision: str, notes: str) -> ChangeProposal:
        """Steward decision: approve or reject a pending proposal."""
        if proposal_id not in self.queue:
            raise KeyError(f"Proposal {proposal_id} not found in queue.")

        proposal = self.queue[proposal_id]
        if decision.upper() == "APPROVE":
            proposal.status = "APPROVED"
        else:
            proposal.status = "REJECTED"

        proposal.reviewed_by = steward_name
        proposal.reviewed_at = datetime.now(timezone.utc)
        proposal.review_notes = notes
        return proposal
