"""Approval Queue for Governed Metadata Changes."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from cforge.governance.audit import ImmutableAuditLog
from cforge.governance.engine import PolicyEngine, PolicyEvaluationResult


class ChangeProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_id: str
    change_type: str  # UPDATE_DESCRIPTION, ADD_TAG, CHANGE_CERTIFICATION, PROPOSE_RULE
    proposed_by: str
    payload: dict[str, Any]
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, AUTO_APPROVED
    evaluation: PolicyEvaluationResult | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalQueue:
    def __init__(
        self,
        engine: PolicyEngine | None = None,
        store: Any | None = None,
        audit_log: ImmutableAuditLog | None = None,
        persistence_path: Path | None = None,
    ):
        self.engine = engine or PolicyEngine()
        self.store = store
        self.audit_log = audit_log
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.queue: dict[str, ChangeProposal] = {}
        if self.persistence_path and self.persistence_path.exists():
            self._load()

    def _save(self):
        if not self.persistence_path:
            return
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            data = {pid: p.model_dump(mode="json") for pid, p in self.queue.items()}
            self.persistence_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass

    def _load(self):
        try:
            raw = self.persistence_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self.queue = {pid: ChangeProposal.model_validate(p) for pid, p in data.items()}
        except Exception:
            self.queue = {}

    def submit_proposal(
        self, asset_id: str, change_type: str, proposed_by: str, payload: dict[str, Any]
    ) -> ChangeProposal:
        """Submit a proposal, evaluate policies, and either auto-approve or queue for review."""
        eval_result = self.engine.evaluate_write_proposal(payload)

        proposal = ChangeProposal(
            asset_id=asset_id, change_type=change_type, proposed_by=proposed_by, payload=payload, evaluation=eval_result
        )

        if eval_result.can_write:
            proposal.status = "AUTO_APPROVED"
            proposal.reviewed_by = "POLICY_ENGINE_AUTO"
            proposal.reviewed_at = datetime.now(timezone.utc)
            proposal.review_notes = "All policy gates passed with high confidence; auto-approved."
            self._apply_to_store(proposal, steward_name="POLICY_ENGINE_AUTO", notes=proposal.review_notes)
        elif not eval_result.passed:
            proposal.status = "REJECTED"
            proposal.reviewed_by = "POLICY_ENGINE_GATE"
            proposal.reviewed_at = datetime.now(timezone.utc)
            proposal.review_notes = f"Blocked by policies: {[v.message for v in eval_result.violations]}"
        else:
            proposal.status = "PENDING"

        self.queue[proposal.proposal_id] = proposal
        self._save()
        return proposal

    def get_pending(self) -> list[ChangeProposal]:
        """List all proposals currently waiting for human steward review."""
        return [p for p in self.queue.values() if p.status == "PENDING"]

    def _apply_to_store(self, proposal: ChangeProposal, steward_name: str, notes: str):
        """Apply approved change proposal to MetadataStore and record audit log."""
        if self.store is not None:
            try:
                if proposal.change_type == "ADD_TAG":
                    is_pii = proposal.payload.get("is_pii", False)
                    tag_name = proposal.payload.get("tag_name", "PII" if is_pii else "TAG")
                    tag_val = proposal.payload.get("pii_type") or proposal.payload.get("tag_value") or "TRUE"
                    conf = float(proposal.payload.get("confidence", 1.0))
                    self.store.add_tag(
                        asset_id=proposal.asset_id,
                        tag_name=tag_name,
                        tag_value=tag_val,
                        confidence=conf,
                        source=proposal.proposed_by,
                        reason=notes or f"Steward approved change from {proposal.proposed_by}",
                    )
                elif proposal.change_type == "UPDATE_DESCRIPTION":
                    new_desc = proposal.payload.get("description")
                    if new_desc:
                        self.store.upsert_asset(
                            {"asset_id": proposal.asset_id, "description": new_desc},
                            changed_by=steward_name,
                            reason=notes,
                        )
                elif proposal.change_type == "CHANGE_CERTIFICATION":
                    cert = proposal.payload.get("certification_status", "CERTIFIED")
                    self.store.upsert_asset(
                        {"asset_id": proposal.asset_id, "certification_status": cert},
                        changed_by=steward_name,
                        reason=notes,
                    )
            except Exception:
                pass

        if self.audit_log is not None:
            try:
                evaluated_policies = (
                    [v.policy_id for v in proposal.evaluation.violations] if proposal.evaluation else ["POL-002"]
                )
                self.audit_log.append(
                    actor=steward_name,
                    asset_id=proposal.asset_id,
                    action=f"PROPOSAL_{proposal.status}",
                    policies_evaluated=evaluated_policies,
                    before_state={"status": "PENDING"},
                    after_state={"status": proposal.status, "payload": proposal.payload},
                )
            except Exception:
                pass

    def review_proposal(self, proposal_id: str, steward_name: str, decision: str, notes: str) -> ChangeProposal:
        """Steward decision: approve or reject a pending proposal."""
        if proposal_id not in self.queue:
            raise KeyError(f"Proposal {proposal_id} not found in queue.")

        proposal = self.queue[proposal_id]
        if decision.upper() == "APPROVE":
            proposal.status = "APPROVED"
            proposal.reviewed_by = steward_name
            proposal.reviewed_at = datetime.now(timezone.utc)
            proposal.review_notes = notes
            self._apply_to_store(proposal, steward_name=steward_name, notes=notes)
        else:
            proposal.status = "REJECTED"
            proposal.reviewed_by = steward_name
            proposal.reviewed_at = datetime.now(timezone.utc)
            proposal.review_notes = notes
            if self.audit_log is not None:
                evaluated_policies = (
                    [v.policy_id for v in proposal.evaluation.violations] if proposal.evaluation else ["POL-002"]
                )
                self.audit_log.append(
                    actor=steward_name,
                    asset_id=proposal.asset_id,
                    action="PROPOSAL_REJECTED",
                    policies_evaluated=evaluated_policies,
                    before_state={"status": "PENDING"},
                    after_state={"status": "REJECTED", "notes": notes},
                )

        self._save()
        return proposal
