"""Immutable Cryptographic Audit Trail for Governance Actions."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class AuditRecord(BaseModel):
    record_id: int
    prev_hash: str
    curr_hash: str
    timestamp: str
    actor: str
    asset_id: str
    action: str
    policy_ids_evaluated: list[str]
    before_state: dict[str, Any] | None
    after_state: dict[str, Any]
    diff: dict[str, Any]


class ImmutableAuditLog:
    def __init__(self, persistence_path: Path | None = None):
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.chain: list[AuditRecord] = []
        if self.persistence_path and self.persistence_path.exists():
            self._load()
        else:
            self._genesis()
            if self.persistence_path:
                self._save()

    def _genesis(self):
        genesis_hash = hashlib.sha256(b"CFORGE_GENESIS_ROOT").hexdigest()
        self.chain.append(
            AuditRecord(
                record_id=0,
                prev_hash="0" * 64,
                curr_hash=genesis_hash,
                timestamp=datetime.now(timezone.utc).isoformat(),
                actor="SYSTEM_BOOTSTRAP",
                asset_id="cforge.root",
                action="GENESIS",
                policy_ids_evaluated=[],
                before_state=None,
                after_state={"status": "INITIALIZED"},
                diff={"genesis": True},
            )
        )

    def _save(self):
        if not self.persistence_path:
            return
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
            data = [rec.model_dump() for rec in self.chain]
            self.persistence_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception:
            pass

    def _load(self):
        try:
            raw = self.persistence_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self.chain = [AuditRecord.model_validate(item) for item in data]
            if not self.chain:
                self._genesis()
                self._save()
        except Exception:
            self.chain = []
            self._genesis()
            self._save()

    def append(
        self,
        actor: str,
        asset_id: str,
        action: str,
        policies_evaluated: list[str],
        before_state: dict[str, Any] | None,
        after_state: dict[str, Any],
    ) -> AuditRecord:
        """Append an immutable audit entry with SHA-256 hash chaining."""
        prev_record = self.chain[-1]
        rec_id = len(self.chain)
        t_now = datetime.now(timezone.utc).isoformat()

        # Compute field diff
        diff: dict[str, Any] = {}
        if before_state:
            for k, v in after_state.items():
                if before_state.get(k) != v:
                    diff[k] = {"before": before_state.get(k), "after": v}
        else:
            diff = {"created": after_state}

        payload = {
            "record_id": rec_id,
            "prev_hash": prev_record.curr_hash,
            "timestamp": t_now,
            "actor": actor,
            "asset_id": asset_id,
            "action": action,
            "policies": sorted(policies_evaluated),
            "diff": diff,
        }

        serialized = json.dumps(payload, sort_keys=True)
        curr_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        record = AuditRecord(
            record_id=rec_id,
            prev_hash=prev_record.curr_hash,
            curr_hash=curr_hash,
            timestamp=t_now,
            actor=actor,
            asset_id=asset_id,
            action=action,
            policy_ids_evaluated=policies_evaluated,
            before_state=before_state,
            after_state=after_state,
            diff=diff,
        )
        self.chain.append(record)
        self._save()
        return record

    def verify_integrity(self) -> bool:
        """Cryptographically verify the entire audit log hash chain."""
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.prev_hash != prev.curr_hash:
                return False

            payload = {
                "record_id": curr.record_id,
                "prev_hash": curr.prev_hash,
                "timestamp": curr.timestamp,
                "actor": curr.actor,
                "asset_id": curr.asset_id,
                "action": curr.action,
                "policies": sorted(curr.policy_ids_evaluated),
                "diff": curr.diff,
            }
            recomputed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
            if recomputed != curr.curr_hash:
                return False
        return True
